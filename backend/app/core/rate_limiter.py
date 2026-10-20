"""
Sliding-Window In-Memory Rate Limiter Middleware for FastAPI (Phase 21: Security Hardening).
Protects authentication endpoints against brute-force attacks and resource-heavy processing
endpoints against denial-of-service (DoS) attempts.
"""
import time
import logging
from collections import defaultdict
from typing import Dict, List, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Endpoint-specific rate limits: (max_requests, window_seconds)
RATE_LIMIT_RULES: Dict[str, Tuple[int, int]] = {
    "/api/auth/login": (10, 60),      # Max 10 login attempts per minute per IP
    "/api/auth/register": (10, 60),   # Max 10 account registrations per minute per IP
    "/api/resumes/upload": (30, 60),  # Max 30 file uploads per minute per IP
    "/api/resumes/process": (20, 60), # Max 20 pipeline executions per minute per IP
    "/api/jobs/parse": (30, 60),      # Max 30 job parsing requests per minute per IP
}

# Default rate limit for other API endpoints
DEFAULT_RATE_LIMIT: Tuple[int, int] = (180, 60)  # 180 requests per minute per IP


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter tracking request timestamps per client IP and path prefix.
    """

    def __init__(self, app):
        super().__init__(app)
        # client_ip:path -> list of request timestamps
        self._request_history: Dict[str, List[float]] = defaultdict(list)
        self._last_cleanup = time.time()

    def _cleanup_old_records(self, now: float) -> None:
        """Periodic cleanup of expired rate limiting buckets to prevent memory leaks."""
        if now - self._last_cleanup > 300:  # Every 5 minutes
            for key in list(self._request_history.keys()):
                self._request_history[key] = [
                    t for t in self._request_history[key] if now - t < 120
                ]
                if not self._request_history[key]:
                    del self._request_history[key]
            self._last_cleanup = now

    async def dispatch(self, request: Request, call_next):
        # Only rate-limit API routes
        path = request.url.path
        if not path.startswith("/api") or path.startswith("/api/health"):
            return await call_next(request)

        # Extract client IP (handling X-Forwarded-For if behind a proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "127.0.0.1"

        now = time.time()
        self._cleanup_old_records(now)

        # Match path rule
        rule = None
        for rule_path, limit in RATE_LIMIT_RULES.items():
            if path.startswith(rule_path):
                rule = limit
                break

        max_requests, window_seconds = rule if rule else DEFAULT_RATE_LIMIT
        bucket_key = f"{client_ip}:{path}"

        # Prune timestamps outside current window
        history = self._request_history[bucket_key]
        window_start = now - window_seconds
        valid_timestamps = [t for t in history if t > window_start]
        self._request_history[bucket_key] = valid_timestamps

        if len(valid_timestamps) >= max_requests:
            retry_after = int(window_seconds - (now - valid_timestamps[0])) + 1
            logger.warning(
                "Rate limit exceeded for IP '%s' on path '%s' (%d/%d in %ds)",
                client_ip,
                path,
                len(valid_timestamps),
                max_requests,
                window_seconds,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Too many requests. Please slow down and try again.",
                    "retry_after_seconds": max(1, retry_after),
                },
                headers={"Retry-After": str(max(1, retry_after))},
            )

        # Record this request
        self._request_history[bucket_key].append(now)

        response = await call_next(request)
        return response
