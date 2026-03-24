"""
SOP App - Authentication routes.
Driver and admin login endpoints.
"""
import datetime
import secrets
import logging

import httpx
from fastapi import APIRouter, Request, HTTPException

from database import get_db, verify_pin
from config import settings
from middleware.auth import get_client_ip
from middleware.security import check_rate_limit, record_login_attempt
from models.requests import DriverLoginRequest, AdminLoginRequest

router = APIRouter(prefix="/api", tags=["auth"])
logger = logging.getLogger(__name__)


def _log_audit(user_type: str, user_id: int, user_name: str, action: str,
               resource_type: str, resource_id: int | None = None,
               details: str | None = None, ip: str | None = None,
               user_agent: str | None = None, session_id: str | None = None,
               request_path: str | None = None,
               geo_city: str | None = None, geo_region: str | None = None,
               geo_country: str | None = None):
    conn = get_db()
    conn.execute(
        """INSERT INTO audit_log
           (user_type, user_id, user_name, action, resource_type, resource_id,
            details, ip_address, user_agent, session_id, request_path,
            geo_city, geo_region, geo_country)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (user_type, user_id, user_name, action, resource_type, resource_id,
         details, ip, user_agent, session_id, request_path,
         geo_city, geo_region, geo_country)
    )
    conn.commit()
    conn.close()


async def _geolocate_ip(ip: str) -> dict:
    """Geolocate an IP address using ip-api.com (free, 45 req/min)."""
    if ip in ("127.0.0.1", "unknown", "::1", "localhost"):
        return {}
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"http://ip-api.com/json/{ip}?fields=city,regionName,country")
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "geo_city": data.get("city", ""),
                    "geo_region": data.get("regionName", ""),
                    "geo_country": data.get("country", ""),
                }
    except Exception:
        logger.debug(f"Geolocation failed for {ip}")
    return {}


def _create_session(user_type: str, user_id: int, user_name: str,
                    ttl_seconds: int, ip: str, geo: dict) -> str:
    token = secrets.token_hex(32)
    expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=ttl_seconds)
    conn = get_db()
    conn.execute(
        """INSERT INTO sessions (token, user_type, user_id, user_name, ip_address,
           geo_city, geo_region, geo_country, expires_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (token, user_type, user_id, user_name, ip,
         geo.get("geo_city"), geo.get("geo_region"), geo.get("geo_country"),
         expires.isoformat())
    )
    conn.commit()
    conn.close()
    return token


@router.post("/driver/login")
async def driver_login(body: DriverLoginRequest, request: Request):
    ip = get_client_ip(request)
    check_rate_limit(ip)

    # Match username as first_initial + last_name, case-insensitive
    conn = get_db()
    driver = conn.execute(
        "SELECT * FROM drivers WHERE LOWER(SUBSTR(first_name,1,1) || last_name) = LOWER(?) AND is_active=1",
        (body.username.strip(),)
    ).fetchone()
    conn.close()

    if not driver or not verify_pin(body.pin, driver["pin_hash"]):
        record_login_attempt(ip)
        _log_audit("driver", 0, body.username, "login_failed", "session",
                   ip=ip, user_agent=request.headers.get("user-agent"),
                   request_path="/api/driver/login")
        raise HTTPException(status_code=401, detail="Invalid username or PIN")

    name = f"{driver['first_name']} {driver['last_name']}"
    geo = await _geolocate_ip(ip)
    token = _create_session("driver", driver["id"], name,
                            settings.DRIVER_SESSION_TTL, ip, geo)

    _log_audit("driver", driver["id"], name, "login", "session",
               ip=ip, user_agent=request.headers.get("user-agent"),
               session_id=token, request_path="/api/driver/login",
               **geo)

    return {"token": token, "driver": {"id": driver["id"], "name": name}}


@router.post("/admin/login")
async def admin_login(body: AdminLoginRequest, request: Request):
    ip = get_client_ip(request)
    check_rate_limit(ip)

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM drivers WHERE id=? AND is_admin=1 AND is_active=1",
        (body.user_id,)
    ).fetchone()
    conn.close()

    if not user or not verify_pin(body.pin, user["pin_hash"]):
        record_login_attempt(ip)
        _log_audit("admin", body.user_id, "", "login_failed", "session",
                   ip=ip, user_agent=request.headers.get("user-agent"),
                   request_path="/api/admin/login")
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    name = f"{user['first_name']} {user['last_name']}"
    geo = await _geolocate_ip(ip)
    token = _create_session("admin", user["id"], name,
                            settings.ADMIN_SESSION_TTL, ip, geo)

    _log_audit("admin", user["id"], name, "login", "session",
               ip=ip, user_agent=request.headers.get("user-agent"),
               session_id=token, request_path="/api/admin/login",
               **geo)

    return {"token": token, "user": {"id": user["id"], "name": name}}
