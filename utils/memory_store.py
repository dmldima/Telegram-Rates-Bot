from typing import Optional, Tuple
from config import USE_REDIS, REDIS_URL
from utils.logger import setup_logger

logger = setup_logger(__name__)

# In-memory storage. When Redis is configured it is the primary store, but we
# also keep every pair here as a per-instance fallback so that a transient
# Redis error never makes a user's pair "disappear" mid-session.
_memory_storage: dict[int, Tuple[str, str]] = {}
_redis_client = None

_REDIS_TTL_SECONDS = 86400 * 30  # 30 days


def _redis_key(user_id: int) -> str:
    return f"user:{user_id}:pair"


if USE_REDIS:
    try:
        # redis.asyncio is non-blocking; the synchronous client would block the
        # event loop on every call, stalling the whole bot during Redis I/O.
        import redis.asyncio as redis
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        logger.info("Redis storage initialized (async)")
    except ImportError:
        logger.warning("Redis not available, using in-memory storage")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")


async def set_pair(user_id: int, base: str, target: str) -> None:
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError(f"Invalid user_id: {user_id}")
    if not base or not target:
        raise ValueError("Currency codes cannot be empty")

    pair = (base.upper(), target.upper())

    # Always keep the in-memory fallback in sync.
    _memory_storage[user_id] = pair

    if _redis_client:
        try:
            value = f"{pair[0]}/{pair[1]}"
            await _redis_client.set(_redis_key(user_id), value, ex=_REDIS_TTL_SECONDS)
            logger.debug(f"Stored pair for user {user_id} in Redis: {value}")
            return
        except Exception as e:
            logger.error(f"Redis error, falling back to memory: {e}")

    logger.debug(f"Stored pair for user {user_id} in memory: {pair}")


async def get_pair(user_id: int) -> Optional[Tuple[str, str]]:
    if not isinstance(user_id, int) or user_id <= 0:
        return None

    if _redis_client:
        try:
            value = await _redis_client.get(_redis_key(user_id))
            if value:
                parts = value.split('/')
                if len(parts) == 2:
                    logger.debug(f"Retrieved pair for user {user_id} from Redis: {value}")
                    return (parts[0], parts[1])
        except Exception as e:
            logger.error(f"Redis error, falling back to memory: {e}")

    pair = _memory_storage.get(user_id)
    if pair:
        logger.debug(f"Retrieved pair for user {user_id} from memory: {pair}")
    return pair


async def delete_pair(user_id: int) -> bool:
    deleted = False
    if _redis_client:
        try:
            result = await _redis_client.delete(_redis_key(user_id))
            deleted = result > 0
        except Exception as e:
            logger.error(f"Redis error: {e}")

    if user_id in _memory_storage:
        del _memory_storage[user_id]
        deleted = True
    return deleted


async def get_stats() -> dict:
    stats = {
        "backend": "redis" if _redis_client else "memory",
        "users_count": len(_memory_storage)
    }
    if _redis_client:
        try:
            # SCAN instead of KEYS: KEYS is O(N) and blocks the Redis server on
            # large keyspaces.
            count = 0
            async for _ in _redis_client.scan_iter(match="user:*:pair"):
                count += 1
            stats["users_count"] = count
        except Exception as e:
            logger.error(f"Redis error while collecting stats: {e}")
    return stats
