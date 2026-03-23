"""
SOP App - Security middleware.
Rate limiting, security headers.
"""
import datetime
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from config import settings
from database import get_db


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


def check_rate_limit(ip_address: str):
    """Check if IP has exceeded login attempt limit. Raises 429 if so."""
    conn = get_db()
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=settings.LOGIN_WINDOW_SECONDS)
    count = conn.execute(
        "SELECT COUNT(*) FROM login_attempts WHERE ip_address=? AND attempted_at > ?",
        (ip_address, cutoff.isoformat())
    ).fetchone()[0]
    conn.close()
    if count >= settings.MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Try again in {settings.LOGIN_WINDOW_SECONDS // 60} minutes."
        )


def record_login_attempt(ip_address: str):
    """Record a failed login attempt for rate limiting."""
    conn = get_db()
    conn.execute("INSERT INTO login_attempts (ip_address) VALUES (?)", (ip_address,))
    conn.commit()
    # Clean up old attempts (older than 1 hour)
    conn.execute(
        "DELETE FROM login_attempts WHERE attempted_at < datetime('now', '-1 hour')"
    )
    conn.commit()
    conn.close()
