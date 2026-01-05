import logging
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis client will be created lazily on first use so imports don't block
redis_client = None
_redis_available = False


def _ensure_redis_client() -> None:
    """Attempt to create a Redis client with short timeouts.

    This is intentionally lazy to avoid blocking at import time when
    Redis is not available (e.g. in test environments or CI).
    """
    global redis_client, _redis_available
    if redis_client is not None or _redis_available:
        return

    try:
        # Short timeouts so attempts fail fast
        redis_client = redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        try:
            redis_client.ping()
            _redis_available = True
        except Exception:
            redis_client = None
            _redis_available = False
            logger.debug("Redis is not available at %s; caching disabled", settings.REDIS_URL)
    except Exception as e:
        redis_client = None
        _redis_available = False
        logger.debug("Could not create Redis client: %s; caching disabled", e)


def get_inventory_quantity(product_id: int):
    """Return cached quantity or None. Fail silently if Redis is unavailable."""
    _ensure_redis_client()
    if not _redis_available:
        return None
    key = f"inventory:quantity:{product_id}"
    try:
        quantity = redis_client.get(key)
        return int(quantity) if quantity else None
    except Exception as e:
        logger.warning("Redis GET failed for %s: %s", key, e)
        return None


def set_inventory_quantity(product_id: int, quantity: int):
    """Set cached quantity; ignore failures."""
    _ensure_redis_client()
    if not _redis_available:
        return
    key = f"inventory:quantity:{product_id}"
    try:
        redis_client.set(key, quantity)
    except Exception as e:
        logger.warning("Redis SET failed for %s: %s", key, e)


def delete_inventory_quantity(product_id: int):
    """Delete cached quantity; ignore failures."""
    _ensure_redis_client()
    if not _redis_available:
        return
    key = f"inventory:quantity:{product_id}"
    try:
        redis_client.delete(key)
    except Exception as e:
        logger.warning("Redis DEL failed for %s: %s", key, e)
