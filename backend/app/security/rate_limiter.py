import time
from typing import Optional
from app.core.redis import get_redis_client
from app.core.config import settings
from fastapi import HTTPException, status

class RateLimiter:
    @staticmethod
    async def check_rate_limit(user_id: str, limit: int = settings.RATE_LIMIT_PER_MINUTE) -> None:
        redis = await get_redis_client()
        if redis is None:
            return # Skip if Redis unavailable

        key = f"rate_limit:{user_id}:{int(time.time() // 60)}"
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 60)

        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "RATE_LIMIT_EXCEEDED", "message": f"Rate limit of {limit} requests/minute exceeded."}
            )
