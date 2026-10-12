import asyncio
import os
import shutil
import sys
import tempfile
import uuid
import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.redis import get_redis_client, check_redis_health, close_redis_client
from app.models.workspace import Workspace
from app.models.repository import Repository, IndexStatus
from app.models.file import RepositoryFile, CodeChunk
from app.security.rate_limiter import RateLimiter
from app.task_queue.redis_queue import (
    RedisJobQueue,
    JobStatus,
    DuplicateJobError,
    RedisQueueUnavailableError,
)


@pytest_asyncio.fixture(autouse=True)
async def cleanup_redis_connection():
    """Ensure each test runs with a fresh connection matching its own event loop and clean queue."""
    redis = await get_redis_client()
    if redis:
        keys = await redis.keys("codepilot:*")
        if keys:
            await redis.delete(*keys)
    yield
    if redis:
        keys = await redis.keys("codepilot:*")
        if keys:
            await redis.delete(*keys)
    await close_redis_client()


@pytest.mark.asyncio
async def test_live_redis_health_check():
    """Verify health check against the live local Redis instance."""
    health = await check_redis_health()
    assert health["configured"] is True
    assert health["connected"] is True
    assert health["ping_ms"] is not None and health["ping_ms"] >= 0
    assert health["version"] is not None
    assert health["mode"] == "standalone"
    assert "indexing_queue_depth" in health
    assert "active_workers" in health


@pytest.mark.asyncio
async def test_live_redis_rate_limiter_atomic_concurrency():
    """Verify atomic distributed rate limiting against real Redis under concurrent requests."""
    redis = await get_redis_client()
    assert redis is not None, "Real Redis must be running for this test"

    test_user_id = f"test_user_{uuid.uuid4().hex[:6]}"

    try:
        # Run 5 concurrent requests with limit=5 -> all succeed
        tasks = [RateLimiter.check_rate_limit(user_id=test_user_id, limit=5) for _ in range(5)]
        await asyncio.gather(*tasks)

        status = RateLimiter.get_status()
        assert status["is_distributed"] is True
        assert status["mode"] == "redis"

        # 6th request must trigger HTTP 429
        with pytest.raises(HTTPException) as exc:
            await RateLimiter.check_rate_limit(user_id=test_user_id, limit=5)
        assert exc.value.status_code == 429
        assert exc.value.detail["code"] == "RATE_LIMIT_EXCEEDED"

    finally:
        # Cleanup test rate limit keys in Redis
        keys = await redis.keys(f"rate_limit:{test_user_id}:*")
        if keys:
            await redis.delete(*keys)


@pytest.mark.asyncio
async def test_live_redis_enqueue_and_deduplication():
    """Verify job enqueueing, metadata storage, and duplicate prevention in real Redis."""
    redis = await get_redis_client()
    assert redis is not None

    test_repo_id = f"repo_test_{uuid.uuid4().hex[:8]}"
    test_user_id = "test_developer_1"

    try:
        # 1. Enqueue job
        job = await RedisJobQueue.enqueue_indexing_job(
            repository_id=test_repo_id,
            user_id=test_user_id,
            source_dir="."
        )
        assert job["repository_id"] == test_repo_id
        assert job["status"] == JobStatus.QUEUED.value

        # 2. Verify stored in Redis hash
        stored_job = await RedisJobQueue.get_job(job["id"])
        assert stored_job is not None
        assert stored_job["repository_id"] == test_repo_id
        assert stored_job["stage"] == "QUEUED"

        # 3. Verify deduplication lock prevents parallel enqueue of same repo
        with pytest.raises(DuplicateJobError) as exc_info:
            await RedisJobQueue.enqueue_indexing_job(
                repository_id=test_repo_id,
                user_id=test_user_id,
                source_dir="."
            )
        assert "already in progress" in str(exc_info.value)

    finally:
        # Cleanup Redis test keys
        if 'job' in locals():
            await redis.delete(f"{RedisJobQueue.JOB_KEY_PREFIX}{job['id']}")
            await redis.lrem(RedisJobQueue.QUEUE_KEY, 0, job["id"])
        await RedisJobQueue.release_lock(test_repo_id, job["id"] if 'job' in locals() else "dummy")


@pytest.mark.asyncio
async def test_live_worker_process_e2e_execution():
    """
    Full end-to-end multi-process integration test:
    1. Sets up a temporary code directory and synthetic Repository in SQLite.
    2. Enqueues job into real Redis queue.
    3. Spawns a dedicated worker process (python -m app.worker).
    4. Worker BRPOPs job, indexes repository, saves chunks to SQLite, updates Redis status.
    5. Verifies completed status, chunk records in SQLite, and lock release.
    6. Shuts down worker gracefully.
    """
    redis = await get_redis_client()
    assert redis is not None, "Redis instance required"

    # 1. Create temporary directory with a test Python file
    temp_dir = tempfile.mkdtemp(prefix="codepilot_test_repo_")
    test_file_path = os.path.join(temp_dir, "calculator.py")
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write('''"""Test Calculator Module."""

def add_numbers(a: int, b: int) -> int:
    """Adds two integers."""
    return a + b

class MathService:
    """Service performing mathematical operations."""
    def multiply(self, x: int, y: int) -> int:
        return x * y
''')

    test_repo_id = f"worker_test_{uuid.uuid4().hex[:8]}"

    # 2. Insert synthetic repository in database linked to existing workspace
    async with AsyncSessionLocal() as db:
        ws_res = await db.execute(select(Workspace))
        ws = ws_res.scalars().first()
        ws_id = ws.id if ws else "default-ws"

        repo = Repository(
            id=test_repo_id,
            workspace_id=ws_id,
            name="Worker Test Repository",
            description="Integration test repo for multi-process worker",
            github_url=None,
            default_branch="main",
            status=IndexStatus.PENDING
        )
        db.add(repo)
        await db.commit()

    # 3. Enqueue indexing job into real Redis
    job = await RedisJobQueue.enqueue_indexing_job(
        repository_id=test_repo_id,
        user_id="test_user",
        source_dir=temp_dir,
        max_retries=1
    )
    job_id = job["id"]

    # 4. Spawn a real worker process as a separate OS process
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    worker_env = os.environ.copy()
    worker_env["QUEUE_MODE"] = "redis"
    worker_env["LLM_PROVIDER"] = "mock"
    worker_env["EMBEDDING_PROVIDER"] = "mock"  # Keep integration test fast & deterministic
    worker_env["PYTHONPATH"] = backend_dir

    worker_log_path = os.path.join(tempfile.gettempdir(), f"worker_{uuid.uuid4().hex[:6]}.log")
    worker_log_file = open(worker_log_path, "w", encoding="utf-8")

    worker_proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "app.worker",
        cwd=backend_dir,
        env=worker_env,
        stdout=worker_log_file,
        stderr=worker_log_file
    )

    try:
        # 5. Wait for worker process to pick up job and complete it (poll up to 30s)
        completed = False
        job_state = None
        for _ in range(60):
            await asyncio.sleep(0.5)
            job_state = await RedisJobQueue.get_job(job_id)
            if job_state and job_state.get("status") == JobStatus.COMPLETED.value:
                completed = True
                break

        if not completed:
            worker_log_file.flush()
            with open(worker_log_path, "r", encoding="utf-8", errors="ignore") as lf:
                log_content = lf.read()
            assert completed, f"Job {job_id} did not reach COMPLETED. State: {job_state}\nWorker logs:\n{log_content}"

        # 6. Verify database records
        async with AsyncSessionLocal() as db:
            db_repo = await db.get(Repository, test_repo_id)
            assert db_repo is not None
            assert db_repo.status == IndexStatus.COMPLETED
            assert db_repo.indexed_files_count >= 1
            assert db_repo.indexed_chunks_count >= 1

            # Verify chunks were written
            stmt = select(CodeChunk).where(CodeChunk.repository_id == test_repo_id)
            chunks = (await db.execute(stmt)).scalars().all()
            assert len(chunks) >= 1

        # 7. Verify deduplication lock was released after completion
        lock_val = await redis.get(f"{RedisJobQueue.LOCK_KEY_PREFIX}{test_repo_id}")
        assert lock_val is None, "Lock should be released after job completion"

    finally:
        # Gracefully terminate the worker subprocess
        try:
            worker_proc.terminate()
            await asyncio.wait_for(worker_proc.wait(), timeout=3.0)
        except Exception:
            worker_proc.kill()

        # Clean up database records
        async with AsyncSessionLocal() as db:
            del_chunks_stmt = select(CodeChunk).where(CodeChunk.repository_id == test_repo_id)
            chunks_to_del = (await db.execute(del_chunks_stmt)).scalars().all()
            for ch in chunks_to_del:
                await db.delete(ch)
            del_files_stmt = select(RepositoryFile).where(RepositoryFile.repository_id == test_repo_id)
            files_to_del = (await db.execute(del_files_stmt)).scalars().all()
            for fi in files_to_del:
                await db.delete(fi)
            db_repo = await db.get(Repository, test_repo_id)
            if db_repo:
                await db.delete(db_repo)
            await db.commit()

        # Clean up filesystem
        try:
            worker_log_file.close()
        except Exception:
            pass
        shutil.rmtree(temp_dir, ignore_errors=True)

        # Clean up Redis job key
        await redis.delete(f"{RedisJobQueue.JOB_KEY_PREFIX}{job_id}")


@pytest.mark.asyncio
async def test_live_worker_retry_and_failure_policy():
    """Verify bounded retry policy, stage updates, and lock release upon terminal failure."""
    redis = await get_redis_client()
    assert redis is not None

    fail_repo_id = f"fail_repo_{uuid.uuid4().hex[:8]}"

    # Enqueue a job with max_retries = 1 pointing to a non-existent directory
    job = await RedisJobQueue.enqueue_indexing_job(
        repository_id=fail_repo_id,
        user_id="test_user",
        source_dir="/invalid/directory/path/does/not/exist",
        max_retries=1
    )
    job_id = job["id"]

    try:
        from app.worker import IndexingWorker
        worker = IndexingWorker(worker_id="test_retry_worker")

        # 1. First execution attempt -> should fail and re-enqueue with retry_count=1
        await worker.process_job(job_id)

        job_state = await RedisJobQueue.get_job(job_id)
        assert job_state is not None
        assert job_state["status"] == JobStatus.QUEUED.value
        assert job_state["stage"] == "RETRYING"
        assert job_state["retry_count"] == 1

        # Lock must still be held during retry backoff
        lock_val = await redis.get(f"{RedisJobQueue.LOCK_KEY_PREFIX}{fail_repo_id}")
        assert lock_val == job_id

        # 2. Second execution attempt -> reaches max_retries=1 -> terminal FAILED
        await worker.process_job(job_id)

        final_job = await RedisJobQueue.get_job(job_id)
        assert final_job is not None
        assert final_job["status"] == JobStatus.FAILED.value
        assert final_job["stage"] == "FAILED"
        assert final_job["error"] is not None

        # Lock MUST be released after terminal failure
        final_lock = await redis.get(f"{RedisJobQueue.LOCK_KEY_PREFIX}{fail_repo_id}")
        assert final_lock is None, "Deduplication lock must be released after terminal failure"

    finally:
        await redis.delete(f"{RedisJobQueue.JOB_KEY_PREFIX}{job_id}")
        await redis.lrem(RedisJobQueue.QUEUE_KEY, 0, job_id)
        await RedisJobQueue.release_lock(fail_repo_id, job_id)


@pytest.mark.asyncio
async def test_live_worker_crash_and_orphaned_job_recovery():
    """
    Verify worker crash handling and orphaned job recovery:
    1. Worker abruptly dies while processing (simulated by abandoning a RUNNING job).
    2. Crash recovery detects the stalled job, increments retry_count, and re-enqueues into FIFO.
    3. Second crash exceeds max_retries: terminal failure, lock release, and DB status update.
    """
    import time
    redis = await get_redis_client()
    assert redis is not None

    crash_repo_id = f"crash_repo_{uuid.uuid4().hex[:8]}"

    # 1. Enqueue job
    job = await RedisJobQueue.enqueue_indexing_job(
        repository_id=crash_repo_id,
        user_id="test_user",
        source_dir=".",
        max_retries=1
    )
    job_id = job["id"]

    try:
        # 2. Simulate worker picking up job and then crashing mid-execution
        await RedisJobQueue.update_job_status(job_id, JobStatus.RUNNING, stage="PARSING")
        # Backdate the active job timestamp by 100 seconds to simulate elapsed execution timeout
        await redis.zadd(RedisJobQueue.ACTIVE_JOBS_KEY, {job_id: time.time() - 100})

        # 3. Crash recovery detects abandoned job (timeout threshold = 30s)
        recovered = await RedisJobQueue.recover_orphaned_jobs(timeout_seconds=30)
        assert job_id in recovered

        # Verify job was re-enqueued for retry
        recovered_job = await RedisJobQueue.get_job(job_id)
        assert recovered_job["status"] == JobStatus.QUEUED.value
        assert recovered_job["stage"] == "RECOVERED_RETRY"
        assert recovered_job["retry_count"] == 1
        assert await redis.llen(RedisJobQueue.QUEUE_KEY) >= 1

        # 4. Simulate worker picking up job again and crashing again
        # Pop from queue
        await redis.brpop(RedisJobQueue.QUEUE_KEY, timeout=1)
        await RedisJobQueue.update_job_status(job_id, JobStatus.RUNNING, stage="EMBEDDING")
        await redis.zadd(RedisJobQueue.ACTIVE_JOBS_KEY, {job_id: time.time() - 100})

        # 5. Crash recovery runs again -> retry_count (1) >= max_retries (1) -> terminal FAILED
        recovered_second = await RedisJobQueue.recover_orphaned_jobs(timeout_seconds=30)
        assert job_id in recovered_second

        final_job = await RedisJobQueue.get_job(job_id)
        assert final_job["status"] == JobStatus.FAILED.value
        assert final_job["stage"] == "FAILED"
        assert "timeout" in final_job["error"].lower() or "retries" in final_job["error"].lower()

        # Deduplication lock MUST be released
        lock = await redis.get(f"{RedisJobQueue.LOCK_KEY_PREFIX}{crash_repo_id}")
        assert lock is None, "Lock must be released upon terminal crash recovery"

    finally:
        await redis.delete(f"{RedisJobQueue.JOB_KEY_PREFIX}{job_id}")
        await redis.lrem(RedisJobQueue.QUEUE_KEY, 0, job_id)
        await redis.zrem(RedisJobQueue.ACTIVE_JOBS_KEY, job_id)
        await RedisJobQueue.release_lock(crash_repo_id, job_id)
