import json
import logging
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List

from app.core.redis import get_redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobError(Exception):
    """Base exception for job queue errors."""
    pass


class DuplicateJobError(JobError):
    """Raised when an indexing job for the repository is already running or queued."""
    pass


class RedisQueueUnavailableError(JobError):
    """Raised when Redis is configured as queue backend but cannot be reached."""
    pass


class RedisJobQueue:
    """
    Production-grade Redis-backed asynchronous job queue for CodePilot AI.
    Handles job enqueuing, distributed deduplication locking, status inspection,
    and worker orchestration.
    """

    QUEUE_KEY = "codepilot:queue:indexing"
    JOB_KEY_PREFIX = "codepilot:job:"
    LOCK_KEY_PREFIX = "codepilot:lock:index:"
    WORKER_PREFIX = "codepilot:workers:"
    ACTIVE_JOBS_KEY = "codepilot:jobs:active"
    JOB_TTL_SECONDS = 86400  # 24 hours
    LOCK_TTL_SECONDS = 300   # 5 minutes lock expiry

    @classmethod
    async def enqueue_indexing_job(
        cls,
        repository_id: str,
        user_id: str,
        source_dir: str,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Validates duplicate locks, creates a persistent job record in Redis,
        and enqueues the job ID for worker processing.
        """
        redis = await get_redis_client()
        if redis is None:
            raise RedisQueueUnavailableError("Redis is unreachable. Cannot enqueue job.")

        job_id = f"job_{uuid.uuid4().hex[:12]}"
        lock_key = f"{cls.LOCK_KEY_PREFIX}{repository_id}"

        # 1. Acquire distributed lock (prevents concurrent duplicate jobs on same repo)
        acquired = await redis.set(lock_key, job_id, nx=True, ex=cls.LOCK_TTL_SECONDS)
        if not acquired:
            active_job_id = await redis.get(lock_key)
            raise DuplicateJobError(
                f"Indexing is already in progress for repository '{repository_id}' (active job: {active_job_id})."
            )

        # 2. Persist job metadata in Redis Hash
        job_data = {
            "id": job_id,
            "repository_id": repository_id,
            "user_id": user_id,
            "source_dir": source_dir,
            "status": JobStatus.QUEUED.value,
            "stage": "QUEUED",
            "retry_count": "0",
            "max_retries": str(max_retries),
            "created_at": datetime.utcnow().isoformat(),
            "started_at": "",
            "completed_at": "",
            "error": ""
        }

        job_key = f"{cls.JOB_KEY_PREFIX}{job_id}"
        await redis.hset(job_key, mapping=job_data)
        await redis.expire(job_key, cls.JOB_TTL_SECONDS)

        # 3. Push to queue (FIFO list via LPUSH / BRPOP)
        await redis.lpush(cls.QUEUE_KEY, job_id)

        logger.info("Enqueued indexing job %s for repo %s", job_id, repository_id)
        return job_data

    @classmethod
    async def get_job(cls, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve live job status and metadata from Redis."""
        redis = await get_redis_client()
        if redis is None:
            return None

        job_key = f"{cls.JOB_KEY_PREFIX}{job_id}"
        data = await redis.hgetall(job_key)
        if not data:
            return None

        return {
            "id": data.get("id", job_id),
            "repository_id": data.get("repository_id"),
            "user_id": data.get("user_id"),
            "source_dir": data.get("source_dir"),
            "status": data.get("status", JobStatus.QUEUED.value),
            "stage": data.get("stage", "UNKNOWN"),
            "retry_count": int(data.get("retry_count", 0)),
            "max_retries": int(data.get("max_retries", 2)),
            "created_at": data.get("created_at"),
            "started_at": data.get("started_at") or None,
            "completed_at": data.get("completed_at") or None,
            "error": data.get("error") or None
        }

    @classmethod
    async def update_job_status(
        cls,
        job_id: str,
        status: JobStatus,
        stage: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """Update job execution state in Redis hash."""
        redis = await get_redis_client()
        if redis is None:
            return

        job_key = f"{cls.JOB_KEY_PREFIX}{job_id}"
        updates: Dict[str, str] = {"status": status.value}

        if stage:
            updates["stage"] = stage

        now = datetime.utcnow().isoformat()
        if status == JobStatus.RUNNING:
            updates["started_at"] = now
            try:
                await redis.zadd(cls.ACTIVE_JOBS_KEY, {job_id: time.time()})
            except Exception as exc:
                logger.warning("Failed to record active job in Redis: %s", exc)
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED):
            updates["completed_at"] = now
            try:
                await redis.zrem(cls.ACTIVE_JOBS_KEY, job_id)
            except Exception as exc:
                logger.warning("Failed to remove active job from Redis: %s", exc)

        if error:
            # Store sanitized error without secrets
            updates["error"] = error[:300]

        await redis.hset(job_key, mapping=updates)

    @classmethod
    async def recover_orphaned_jobs(cls, timeout_seconds: int = 300) -> List[str]:
        """
        Scans for jobs stuck in RUNNING state beyond timeout_seconds (e.g. worker process crashed).
        If retry_count < max_retries, increments retry_count and re-enqueues into FIFO queue.
        Otherwise, marks FAILED, releases the lock, and updates DB repository status.
        """
        redis = await get_redis_client()
        if redis is None:
            return []

        cutoff = time.time() - timeout_seconds
        stale_job_ids = await redis.zrangebyscore(cls.ACTIVE_JOBS_KEY, 0, cutoff)
        if not stale_job_ids:
            return []

        recovered: List[str] = []
        for job_id_raw in stale_job_ids:
            job_id = job_id_raw.decode("utf-8") if isinstance(job_id_raw, bytes) else str(job_id_raw)
            job = await cls.get_job(job_id)
            if not job or job.get("status") != JobStatus.RUNNING.value:
                await redis.zrem(cls.ACTIVE_JOBS_KEY, job_id)
                continue

            repo_id = job.get("repository_id")
            retry_count = job.get("retry_count", 0)
            max_retries = job.get("max_retries", 2)

            if retry_count < max_retries:
                new_retry = retry_count + 1
                job_key = f"{cls.JOB_KEY_PREFIX}{job_id}"
                await redis.hset(job_key, mapping={
                    "status": JobStatus.QUEUED.value,
                    "stage": "RECOVERED_RETRY",
                    "retry_count": str(new_retry),
                    "error": "Worker crash recovery: re-enqueued after execution timeout"
                })
                await redis.lpush(cls.QUEUE_KEY, job_id)
                await redis.zrem(cls.ACTIVE_JOBS_KEY, job_id)
                logger.warning(
                    "Recovered orphaned job %s for repo %s (attempt %d/%d) after worker timeout",
                    job_id, repo_id, new_retry, max_retries + 1
                )
            else:
                await cls.update_job_status(
                    job_id,
                    JobStatus.FAILED,
                    stage="FAILED",
                    error="Worker crash recovery: maximum execution timeout / retries exceeded"
                )
                if repo_id:
                    await cls.release_lock(repo_id, job_id)
                    try:
                        from app.core.database import AsyncSessionLocal
                        from app.models.repository import Repository, IndexStatus
                        async with AsyncSessionLocal() as db:
                            repo = await db.get(Repository, repo_id)
                            if repo and repo.status != IndexStatus.COMPLETED:
                                repo.status = IndexStatus.FAILED
                                await db.commit()
                    except Exception as db_exc:
                        logger.error("Failed to update repo status during crash recovery: %s", db_exc)
                logger.error("Orphaned job %s exceeded max retries. Marked as FAILED.", job_id)

            recovered.append(job_id)

        return recovered

    @classmethod
    async def release_lock(cls, repository_id: str, job_id: Optional[str] = None) -> None:
        """Safely release the indexing lock for a repository."""
        redis = await get_redis_client()
        if redis is None:
            return

        lock_key = f"{cls.LOCK_KEY_PREFIX}{repository_id}"
        if job_id:
            # Atomic unlock script: only delete if value matches job_id
            lua_unlock = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            try:
                await redis.eval(lua_unlock, 1, lock_key, job_id)
            except Exception:
                await redis.delete(lock_key)
        else:
            await redis.delete(lock_key)

    @classmethod
    async def get_queue_depth(cls) -> int:
        """Return the count of currently pending jobs in the queue."""
        redis = await get_redis_client()
        if redis is None:
            return 0
        return await redis.llen(cls.QUEUE_KEY)
