"""
SOP App - Authentication middleware.
FastAPI dependencies for session validation.
"""
import datetime
from fastapi import Request, HTTPException

from database import get_db


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _get_valid_session(request: Request) -> dict | None:
    token = request.headers.get("x-session-token", "")
    if not token:
        return None
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM sessions WHERE token=? AND expires_at > datetime('now')",
        (token,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def require_driver(request: Request) -> dict:
    session = _get_valid_session(request)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if session["user_type"] != "driver":
        raise HTTPException(status_code=403, detail="Driver access required")
    return session


def require_admin(request: Request) -> dict:
    session = _get_valid_session(request)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if session["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return session
