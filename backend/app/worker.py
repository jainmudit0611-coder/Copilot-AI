import asyncio
import logging
import os
import signal
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.redis import get_redis_client, close_redis_client
import app.models  # Ensures all SQLAlchemy declarative models are registered
from app.models.repository import Repository, IndexStatus
from app.task_queue.redis_queue import RedisJobQueue, JobStatus
from app.api.repository import run_repository_indexing

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("codepilot.worker")


class IndexingWorker:
    """
    Dedicated background worker process for Redis-backed indexing jobs.
    Listens for jobs, executes AST chunking and embedding pipelines,
    manages worker heartbeats, and handles retries with backoff.
    """

    def __init__(self, worker_id: Optional[str] = None):
        self.worker_id = worker_id or f"worker_{uuid.uuid4().hex[:8]}"
        self.running = False
        self._stop_event = asyncio.Event()

    async def start(self):
        self.running = True
        logger.info("Starting CodePilot Indexing Worker: %s", self.worker_id)
        logger.info("Redis URL: %s | Queue Mode: %s", settings.REDIS_URL, settings.QUEUE_MODE)
        logger.info("LLM Provider: %s | Embedding Provider: %s (%s)",
                    settings.LLM_PROVIDER, settings.EMBEDDING_PROVIDER, settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT)

        # Setup graceful shutdown signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._handle_signal, sig)
            except NotImplementedError:
                # Signal handlers not implemented on Windows event loop for add_signal_handler
                signal.signal(sig, lambda s, f: self._handle_signal(s))

        # Check and recover any orphaned jobs left by crashed worker processes
        try:
            recovered = await RedisJobQueue.recover_orphaned_jobs(timeout_seconds=settings.INDEXING_JOB_TIMEOUT_SECONDS)
            if recovered:
                logger.info("Worker startup: recovered %d orphaned jobs from previous crashes: %s", len(recovered), recovered)
        except Exception as exc:
            logger.warning("Error running worker startup crash recovery: %s", exc)

        # Start worker loop and heartbeat task
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        try:
            await self._work_loop()
        finally:
            self.running = False
            heartbeat_task.cancel()
            await self._cleanup()

    def _handle_signal(self, sig):
        logger.info("Received termination signal %s. Shutting down worker gracefully...", sig)
        self.running = False
        self._stop_event.set()

    async def _heartbeat_loop(self):
        """Periodically update worker presence in Redis so health checks can report active workers."""
        redis = await get_redis_client()
        heartbeat_key = f"{RedisJobQueue.WORKER_PREFIX}{self.worker_id}"
        heartbeat_ticks = 0
        while self.running and not self._stop_event.is_set():
            try:
                if redis:
                    await redis.set(heartbeat_key, datetime.now(timezone.utc).isoformat(), ex=15)
                heartbeat_ticks += 1
                if heartbeat_ticks % 12 == 0:
                    await RedisJobQueue.recover_orphaned_jobs(timeout_seconds=settings.INDEXING_JOB_TIMEOUT_SECONDS)
            except Exception as exc:
                logger.warning("Worker heartbeat failed: %s", exc)
            await asyncio.sleep(5)

        # Remove on exit
        try:
            if redis:
                await redis.delete(heartbeat_key)
        except Exception:
            pass

    async def _work_loop(self):
        """Main queue consumer loop using BRPOP with non-blocking polling."""
        redis = await get_redis_client()
        if not redis:
            logger.error("Unable to connect to Redis. Worker cannot start queue polling.")
            return

        while self.running and not self._stop_event.is_set():
            try:
                # BRPOP from right side of list (FIFO matching LPUSH)
                item = await redis.brpop(RedisJobQueue.QUEUE_KEY, timeout=2)
                if not item:
                    continue

                _, job_id = item
                await self.process_job(job_id)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Error in worker consumer loop: %s", exc)
                await asyncio.sleep(1)

    async def process_job(self, job_id: str):
        """Execute a single indexing job with retry policy and state transitions."""
        logger.info("Worker %s picked up job: %s", self.worker_id, job_id)
        job = await RedisJobQueue.get_job(job_id)
        if not job:
            logger.warning("Job %s not found in Redis metadata. Skipping.", job_id)
            return

        repo_id = job["repository_id"]
        source_dir = job.get("source_dir") or "."
        retry_count = job.get("retry_count", 0)
        max_retries = job.get("max_retries", 2)

        is_retrying = False
        try:
            # Mark job RUNNING
            await RedisJobQueue.update_job_status(job_id, JobStatus.RUNNING, stage="PARSING")

            # Execute existing indexing service pipeline
            logger.info("Executing indexing pipeline for repository %s...", repo_id)
            await run_repository_indexing(repo_id, source_dir, AsyncSessionLocal)

            # Check final repo status in DB
            async with AsyncSessionLocal() as db:
                repo = await db.get(Repository, repo_id)
                if repo and repo.status == IndexStatus.COMPLETED:
                    await RedisJobQueue.update_job_status(job_id, JobStatus.COMPLETED, stage="COMPLETED")
                    logger.info("Job %s COMPLETED successfully. %d chunks indexed.", job_id, repo.indexed_chunks_count)
                else:
                    raise RuntimeError(f"Repository indexing ended with non-completed status: {repo.status if repo else 'None'}")

        except Exception as exc:
            safe_error = f"{type(exc).__name__}: {str(exc)}"[:200]
            logger.error("Job %s failed on attempt %d/%d: %s", job_id, retry_count + 1, max_retries + 1, safe_error)

            if retry_count < max_retries:
                # Retry with backoff
                is_retrying = True
                new_retry = retry_count + 1
                redis = await get_redis_client()
                if redis:
                    await redis.zrem(RedisJobQueue.ACTIVE_JOBS_KEY, job_id)
                    job_key = f"{RedisJobQueue.JOB_KEY_PREFIX}{job_id}"
                    await redis.hset(job_key, mapping={
                        "status": JobStatus.QUEUED.value,
                        "stage": "RETRYING",
                        "retry_count": str(new_retry),
                        "error": safe_error
                    })
                    # Re-enqueue
                    await asyncio.sleep(2 * new_retry)
                    await redis.lpush(RedisJobQueue.QUEUE_KEY, job_id)
                    logger.info("Re-enqueued job %s for retry attempt %d", job_id, new_retry)
                    return

            # Max retries exceeded -> mark FAILED
            await RedisJobQueue.update_job_status(job_id, JobStatus.FAILED, stage="FAILED", error=safe_error)
            async with AsyncSessionLocal() as db:
                repo = await db.get(Repository, repo_id)
                if repo:
                    repo.status = IndexStatus.FAILED
                    await db.commit()
        finally:
            # Safely release the repository lock so future jobs can run (only if not retrying)
            if not is_retrying:
                await RedisJobQueue.release_lock(repo_id, job_id)

    async def _cleanup(self):
        logger.info("Worker %s shutting down cleanly.", self.worker_id)
        await close_redis_client()


async def run_worker():
    worker = IndexingWorker()
    await worker.start()


if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker terminated by user.")
