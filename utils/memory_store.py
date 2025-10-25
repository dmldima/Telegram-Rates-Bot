from typing import Optional, Tuple
from config import USE_REDIS, REDIS_URL
from utils.logger import setup_logger

logger = setup_logger(__name__)

_memory_storage: dict[int, Tuple[str, str]] = {}
_redis_client = None

if USE_REDIS:
    try:
        import redis
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        logger.info("Redis storage initialized")
    except ImportError:
        logger.warning("Redis not available, using in-memory storage")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")

def set_pair(user_id: int, base: str, target: str) -> None:
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError(f"Invalid user_id: {user_id}")
    if not base or not target:
        raise ValueError("Currency codes cannot be empty")
    
    pair = (base.upper(), target.upper())
    
    if _redis_client:
        try:
            key = f"user:{user_id}:pair"
            value = f"{pair[0]}/{pair[1]}"
            _redis_client.set(key, value, ex=86400 * 30)
            logger.debug(f"Stored pair for user {user_id} in Redis: {value}")
            return
        except Exception as e:
            logger.error(f"Redis error, falling back to memory: {e}")
    
    _memory_storage[user_id] = pair
    logger.debug(f"Stored pair for user {user_id} in memory: {pair}")

def get_pair(user_id: int) -> Optional[Tuple[str, str]]:
    if not isinstance(user_id, int) or user_id <= 0:
        return None
    
    if _redis_client:
        try:
            key = f"user:{user_id}:pair"
            value = _redis_client.get(key)
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

def delete_pair(user_id: int) -> bool:
    deleted = False
    if _redis_client:
        try:
            key = f"user:{user_id}:pair"
            result = _redis_client.delete(key)
            deleted = result > 0
        except Exception as e:
            logger.error(f"Redis error: {e}")
    
    if user_id in _memory_storage:
        del _memory_storage[user_id]
        deleted = True
    return deleted

def get_stats() -> dict:
    stats = {
        "backend": "redis" if _redis_client else "memory",
        "users_count": len(_memory_storage)
    }
    if _redis_client:
        try:
            keys = _redis_client.keys("user:*:pair")
            stats["users_count"] = len(keys)
        except Exception:
            pass
    return stats
