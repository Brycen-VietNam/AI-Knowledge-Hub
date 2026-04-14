# Spec: docs/query-endpoint/spec/query-endpoint.spec.md#S003
# Task: S003-T002 — Sliding window RateLimiter using Valkey ZADD/ZCOUNT
# Task: S003-T004 — Fail-open behavior on Valkey error
# Rule: S004 — 60 req/min per user_id sliding window
# Rule: A005 — 429 shape: {"error": {"code": "RATE_LIMIT_EXCEEDED", ...}}
import logging
import time

import valkey.asyncio as valkey

logger = logging.getLogger(__name__)


class RateLimiter:
    """Sliding window rate limiter backed by Valkey sorted sets.

    Key pattern: ratelimit:{resource}:{user_id}
    Algorithm: ZADD (score=ts, member=ts), ZREMRANGEBYSCORE (trim old),
               ZCOUNT (current window count).
    Fail-open: Valkey errors log a warning and allow the request through.
    """

    def __init__(self, resource: str, limit: int = 60, window: int = 60) -> None:
        self.resource = resource
        self.limit = limit
        self.window = window  # seconds

    async def check(
        self, user_id: str, valkey_client
    ) -> tuple[bool, int, int]:
        """Check and record a request against the rate limit.

        Returns:
            (allowed, remaining, reset_ts) where reset_ts is a Unix timestamp
            indicating when the oldest entry in the window expires.
        """
        now = time.time()
        window_start = now - self.window
        reset_ts = int(now) + self.window
        key = f"ratelimit:{self.resource}:{user_id}"

        try:
            async with valkey_client.pipeline(transaction=False) as pipe:
                # Record this request (score=timestamp, member=timestamp as str)
                pipe.zadd(key, {str(now): now})
                # Trim entries older than the sliding window
                pipe.zremrangebyscore(key, 0, window_start)
                # Count entries in current window
                pipe.zcount(key, window_start, "+inf")
                results = await pipe.execute()

            count: int = results[2]
            remaining = max(0, self.limit - count)
            allowed = count <= self.limit
            return allowed, remaining, reset_ts

        except Exception as exc:
            logger.warning(
                "RateLimiter: Valkey error for key=%s — failing open. error=%s",
                key,
                exc,
            )
            # AC6: fail-open — do not reject request on Valkey failure
            return True, self.limit, reset_ts
