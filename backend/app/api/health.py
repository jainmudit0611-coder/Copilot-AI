from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any

from app.core.database import get_db
from app.core.config import settings
from app.core.redis import check_redis_health
from app.security.rate_limiter import RateLimiter

router = APIRouter(prefix="/health", tags=["Health Checks"])


@router.get("", response_model=Dict[str, Any])
async def get_system_health(db: AsyncSession = Depends(get_db)):
    """
    Comprehensive system health check reporting database, Redis queue,
    rate limiting status, and active AI provider configuration.
    """
    # 1. Database check
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {type(exc).__name__}"

    # 2. Redis & Queue check
    redis_health = await check_redis_health()

    # 3. Rate limiter status
    rate_limiter_status = RateLimiter.get_status()

    # Determine overall status
    is_healthy = (db_status == "connected")
    if settings.QUEUE_MODE == "redis":
        is_healthy = is_healthy and redis_health.get("connected", False)

    return {
        "status": "healthy" if is_healthy else "degraded",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database": {
            "status": db_status,
            "type": "sqlite" if "sqlite" in settings.DATABASE_URL else "postgresql"
        },
        "redis": redis_health,
        "rate_limiter": rate_limiter_status,
        "ai_provider": {
            "llm": settings.LLM_PROVIDER,
            "llm_deployment": settings.AZURE_OPENAI_DEPLOYMENT if settings.LLM_PROVIDER == "azure" else "mock",
            "embeddings": settings.EMBEDDING_PROVIDER or settings.LLM_PROVIDER,
            "embedding_deployment": settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT if (settings.EMBEDDING_PROVIDER or settings.LLM_PROVIDER) == "azure" else "mock"
        }
    }


@router.get("/redis", response_model=Dict[str, Any])
async def get_redis_health():
    """Dedicated health check for Redis connectivity, latency, workers, and queues."""
    return await check_redis_health()
