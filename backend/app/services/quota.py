"""Per-user daily application quotas backed by Redis."""
from datetime import datetime, timezone

import redis

from app.config import settings

redis_client = redis.from_url(settings.REDIS_URL)

# Phase 4 defaults. Tune later based on observed platform tolerance.
DAILY_LIMIT = 10


def _quota_key(user_id: int, platform: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"quota:{user_id}:{platform}:{today}"


def get_remaining(user_id: int, platform: str = "naukri") -> int:
    """Return how many applications the user can still submit today."""
    key = _quota_key(user_id, platform)
    used = int(redis_client.get(key) or 0)
    return max(0, DAILY_LIMIT - used)


def try_consume(user_id: int, platform: str = "naukri") -> tuple[bool, int]:
    """
    Atomically increment the counter and report whether the user is under limit.
    Returns (allowed, remaining_after_this_call).
    """
    key = _quota_key(user_id, platform)
    count = redis_client.incr(key)
    if count == 1:
        # First use today — set expiry at end of day (86400s is fine for Phase 4)
        redis_client.expire(key, 86400)

    if count > DAILY_LIMIT:
        # Already over limit. Decrement back so a retry doesn't inflate further.
        redis_client.decr(key)
        return False, 0

    return True, DAILY_LIMIT - count