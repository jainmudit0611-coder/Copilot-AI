import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException

from app.core.config import settings
from app.task_queue.redis_queue import (
    RedisJobQueue,
    JobStatus,
    DuplicateJobError,
    RedisQueueUnavailableError,
)
from app.security.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_redis_queue_unavailable():
    """Test clear failure when Redis is down and enqueue is called."""
    with patch("app.task_queue.redis_queue.get_redis_client", return_value=None):
        with pytest.raises(RedisQueueUnavailableError) as exc_info:
            await RedisJobQueue.enqueue_indexing_job(
                repository_id="repo-123",
                user_id="user-456",
                source_dir="/mock/dir"
            )
        assert "Redis is unreachable" in str(exc_info.value)


@pytest.mark.asyncio
async def test_redis_queue_enqueue_success():
    """Test successful job enqueueing, metadata persistence, and LPUSH."""
    mock_redis = AsyncMock()
    mock_redis.set.return_value = True  # lock acquired
    mock_redis.hset.return_value = True
    mock_redis.expire.return_value = True
    mock_redis.lpush.return_value = 1

    with patch("app.task_queue.redis_queue.get_redis_client", return_value=mock_redis):
        job = await RedisJobQueue.enqueue_indexing_job(
            repository_id="repo-123",
            user_id="user-456",
            source_dir="/mock/dir",
            max_retries=2
        )

        assert job["repository_id"] == "repo-123"
        assert job["user_id"] == "user-456"
        assert job["status"] == JobStatus.QUEUED.value
        assert job["stage"] == "QUEUED"
        assert job["retry_count"] == "0"
        assert "job_" in job["id"]

        # Verify lock was checked with NX
        mock_redis.set.assert_called_once_with(
            "codepilot:lock:index:repo-123",
            job["id"],
            nx=True,
            ex=RedisJobQueue.LOCK_TTL_SECONDS
        )
        # Verify job pushed to list
        mock_redis.lpush.assert_called_once_with(
            RedisJobQueue.QUEUE_KEY,
            job["id"]
        )


@pytest.mark.asyncio
async def test_redis_duplicate_job_prevention():
    """Test duplicate indexing prevention when lock cannot be acquired."""
    mock_redis = AsyncMock()
    mock_redis.set.return_value = False  # Lock acquisition rejected
    mock_redis.get.return_value = "job_existing_999"

    with patch("app.task_queue.redis_queue.get_redis_client", return_value=mock_redis):
        with pytest.raises(DuplicateJobError) as exc_info:
            await RedisJobQueue.enqueue_indexing_job(
                repository_id="repo-123",
                user_id="user-456",
                source_dir="/mock/dir"
            )
        assert "already in progress" in str(exc_info.value)
        assert "job_existing_999" in str(exc_info.value)


@pytest.mark.asyncio
async def test_redis_job_status_transitions():
    """Test updating job execution states in Redis hash."""
    mock_redis = AsyncMock()

    with patch("app.task_queue.redis_queue.get_redis_client", return_value=mock_redis):
        # 1. Update to RUNNING
        await RedisJobQueue.update_job_status("job-1", JobStatus.RUNNING, stage="PARSING")
        mock_redis.hset.assert_called()
        call_args = mock_redis.hset.call_args[1]["mapping"]
        assert call_args["status"] == "running"
        assert call_args["stage"] == "PARSING"
        assert "started_at" in call_args

        # 2. Update to COMPLETED
        await RedisJobQueue.update_job_status("job-1", JobStatus.COMPLETED, stage="COMPLETED")
        call_args = mock_redis.hset.call_args[1]["mapping"]
        assert call_args["status"] == "completed"
        assert "completed_at" in call_args

        # 3. Update to FAILED
        await RedisJobQueue.update_job_status("job-1", JobStatus.FAILED, stage="FAILED", error="OutOfMemoryError")
        call_args = mock_redis.hset.call_args[1]["mapping"]
        assert call_args["status"] == "failed"
        assert call_args["error"] == "OutOfMemoryError"


@pytest.mark.asyncio
async def test_redis_release_lock():
    """Test release lock logic."""
    mock_redis = AsyncMock()
    with patch("app.task_queue.redis_queue.get_redis_client", return_value=mock_redis):
        await RedisJobQueue.release_lock("repo-123", "job-1")
        mock_redis.eval.assert_called_once()


@pytest.mark.asyncio
async def test_rate_limiter_distributed_pipeline():
    """Test distributed rate limiting with atomic pipeline execution."""
    mock_redis = AsyncMock()
    mock_pipe = MagicMock()
    mock_pipe.execute = AsyncMock(return_value=[5, True])  # Count = 5
    mock_redis.pipeline = MagicMock(return_value=mock_pipe)

    with patch("app.security.rate_limiter.get_redis_client", return_value=mock_redis):
        # Under limit -> passes cleanly
        await RateLimiter.check_rate_limit(user_id="test_user", limit=10)
        status = RateLimiter.get_status()
        assert status["is_distributed"] is True
        assert status["mode"] == "redis"

        # Over limit -> raises 429
        mock_pipe.execute.return_value = [15, True]  # Count = 15 > 10
        with pytest.raises(HTTPException) as exc:
            await RateLimiter.check_rate_limit(user_id="test_user", limit=10)
        assert exc.value.status_code == 429
        assert exc.value.detail["code"] == "RATE_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_rate_limiter_memory_fallback():
    """Test graceful in-memory fallback when Redis is offline."""
    with patch("app.security.rate_limiter.get_redis_client", return_value=None):
        # Request under limit passes
        for _ in range(5):
            await RateLimiter.check_rate_limit(user_id="fallback_user", limit=10)
        status = RateLimiter.get_status()
        assert status["is_distributed"] is False
        assert status["mode"] == "in_memory_fallback"

        # 11th request exceeds limit
        for _ in range(5):
            await RateLimiter.check_rate_limit(user_id="fallback_user", limit=10)
        with pytest.raises(HTTPException) as exc:
            await RateLimiter.check_rate_limit(user_id="fallback_user", limit=10)
        assert exc.value.status_code == 429


@pytest.mark.asyncio
async def test_redis_recover_orphaned_jobs_retry():
    """Test crash recovery re-enqueues orphaned jobs when retries remain."""
    mock_redis = AsyncMock()
    mock_redis.zrangebyscore.return_value = ["job-crash-1"]
    mock_redis.hgetall.return_value = {
        "id": "job-crash-1",
        "repository_id": "repo-123",
        "status": "running",
        "stage": "PARSING",
        "retry_count": "0",
        "max_retries": "2",
        "created_at": "2026-01-01T00:00:00"
    }

    with patch("app.task_queue.redis_queue.get_redis_client", return_value=mock_redis):
        recovered = await RedisJobQueue.recover_orphaned_jobs(timeout_seconds=60)
        assert recovered == ["job-crash-1"]

        # Verify retry count was bumped and pushed back to queue
        mock_redis.hset.assert_called()
        mapping = mock_redis.hset.call_args[1]["mapping"]
        assert mapping["status"] == "queued"
        assert mapping["retry_count"] == "1"
        assert mapping["stage"] == "RECOVERED_RETRY"

        mock_redis.lpush.assert_called_once_with(
            RedisJobQueue.QUEUE_KEY,
            "job-crash-1"
        )
        mock_redis.zrem.assert_called_once_with(
            RedisJobQueue.ACTIVE_JOBS_KEY,
            "job-crash-1"
        )


@pytest.mark.asyncio
async def test_redis_recover_orphaned_jobs_terminal_failure():
    """Test crash recovery marks job FAILED and releases lock when max retries exceeded."""
    mock_redis = AsyncMock()
    mock_redis.zrangebyscore.return_value = ["job-crash-2"]
    mock_redis.hgetall.return_value = {
        "id": "job-crash-2",
        "repository_id": "repo-456",
        "status": "running",
        "stage": "PARSING",
        "retry_count": "2",
        "max_retries": "2",
        "created_at": "2026-01-01T00:00:00"
    }

    with patch("app.task_queue.redis_queue.get_redis_client", return_value=mock_redis), \
         patch("app.task_queue.redis_queue.RedisJobQueue.release_lock") as mock_release:
        recovered = await RedisJobQueue.recover_orphaned_jobs(timeout_seconds=60)
        assert recovered == ["job-crash-2"]

        mock_release.assert_called_once_with("repo-456", "job-crash-2")
        mock_redis.zrem.assert_called_once_with(
            RedisJobQueue.ACTIVE_JOBS_KEY,
            "job-crash-2"
        )
