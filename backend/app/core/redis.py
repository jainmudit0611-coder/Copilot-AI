import asyncio
import time
import logging
from typing import Optional, Dict, Any
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> Optional[aioredis.Redis]:
    """
    Get or initialize the shared async Redis client.
    Uses protocol=2 to ensure compatibility across all Redis engines (5.0, 6.0, 7.0+, cloud).
    Returns None if connection fails.
    """
    global redis_client
    if redis_client is not None:
        try:
            curr_loop = asyncio.get_running_loop()
            pool_loop = getattr(getattr(redis_client, "connection_pool", None), "_loop", None)
            if pool_loop is not None and (pool_loop != curr_loop or pool_loop.is_closed()):
                redis_client = None
        except Exception:
            redis_client = None

    if redis_client is None:
        try:
            client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                protocol=2,
                socket_connect_timeout=2.0
            )
            await client.ping()
            redis_client = client
        except Exception as exc:
            logger.warning("Redis connection failed (%s): %s", settings.REDIS_URL, exc)
            redis_client = None
    return redis_client


async def close_redis_client() -> None:
    """Cleanly close the async Redis client connection pool."""
    global redis_client
    if redis_client is not None:
        try:
            await redis_client.aclose()
        except Exception as exc:
            logger.warning("Error closing Redis client: %s", exc)
        finally:
            redis_client = None


async def check_redis_health() -> Dict[str, Any]:
    """
    Comprehensive Redis health check inspecting connectivity, ping latency,
    server version, active workers, and queue depth.
    """
    configured = bool(settings.REDIS_URL)
    result: Dict[str, Any] = {
        "configured": configured,
        "connected": False,
        "queue_mode": settings.QUEUE_MODE,
        "ping_ms": None,
        "version": None,
        "mode": None,
        "active_workers": 0,
        "indexing_queue_depth": 0
    }

    if not configured:
        return result

    try:
        client = await get_redis_client()
        if client is None:
            return result

        t0 = time.time()
        pong = await client.ping()
        ping_ms = round((time.time() - t0) * 1000, 2)

        if pong:
            result["connected"] = True
            result["ping_ms"] = ping_ms

            # Fetch Redis server info
            try:
                info = await client.info("server")
                result["version"] = info.get("redis_version")
                result["mode"] = info.get("redis_mode", "standalone")
            except Exception:
                pass

            # Active workers (registered with codepilot:workers:*)
            try:
                worker_keys = await client.keys("codepilot:workers:*")
                result["active_workers"] = len(worker_keys)
            except Exception:
                pass

            # Queue depth
            try:
                depth = await client.llen("codepilot:queue:indexing")
                result["indexing_queue_depth"] = depth
            except Exception:
                pass
    except Exception as exc:
        logger.warning("Redis health check failed: %s", exc)
        result["connected"] = False

    return result
