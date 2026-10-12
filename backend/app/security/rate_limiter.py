import time
import logging
from typing import Optional, Dict, Tuple, Any
from app.core.redis import get_redis_client
from app.core.config import settings
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# In-process fallback memory store for when Redis is offline
_in_memory_counters: Dict[str, Tuple[int, float]] = {}


class RateLimiter:
    """
    Production-grade shared rate limiter.
    Uses atomic Redis pipelines when Redis is connected;
    explicitly falls back to process memory with warning logs when Redis is offline.
    """

    _last_mode: str = "redis"

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        return {
            "mode": cls._last_mode,
            "limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
            "is_distributed": cls._last_mode == "redis"
        }

    @classmethod
    async def check_rate_limit(
        cls,
        user_id: str,
        limit: int = settings.RATE_LIMIT_PER_MINUTE
    ) -> None:
        redis = await get_redis_client()
        window = int(time.time() // 60)
        key = f"rate_limit:{user_id}:{window}"

        if redis is not None:
            cls._last_mode = "redis"
            try:
                # Atomic increment and TTL expiration using Redis pipeline
                pipe = redis.pipeline(transaction=True)
                pipe.incr(key)
                pipe.expire(key, 60)
                results = await pipe.execute()
                count = results[0]
            except Exception as exc:
                logger.warning("Redis rate limit operation failed: %s. Falling back to memory.", exc)
                cls._last_mode = "in_memory_fallback"
                count = cls._check_in_memory(key)
        else:
            cls._last_mode = "in_memory_fallback"
            count = cls._check_in_memory(key)

        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit of {limit} requests/minute exceeded.",
                    "distributed": cls._last_mode == "redis"
                }
            )

    @classmethod
    def _check_in_memory(cls, key: str) -> int:
        now = time.time()
        # Clean up stale memory entries older than 2 minutes
        stale = [k for k, (_, expire_at) in _in_memory_counters.items() if now > expire_at]
        for k in stale:
            _in_memory_counters.pop(k, None)

        if key in _in_memory_counters:
            current_count, exp = _in_memory_counters[key]
            new_count = current_count + 1
            _in_memory_counters[key] = (new_count, exp)
            return new_count
        else:
            _in_memory_counters[key] = (1, now + 65.0)
            return 1
