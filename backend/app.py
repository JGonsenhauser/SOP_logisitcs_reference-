"""
SOP App - FastAPI Application
Customer SOP reference system for delivery drivers.
Admin: full CRUD on customers + their SOP requirements.
Driver: login, search customers, view SOP cards.
"""
import os
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from config import settings
from database import init_db
from middleware.security import SecurityHeadersMiddleware
from routes import auth, driver, admin, schema

# Logging
logging.basicConfig(
    level=logging.INFO if settings.is_production else logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    logger.info("Database initialized")

    # Clean expired sessions on startup
    from database import get_db
    conn = get_db()
    deleted = conn.execute("DELETE FROM sessions WHERE expires_at < datetime('now')").rowcount
    # Clean old login attempts
    old_attempts = conn.execute("DELETE FROM login_attempts WHERE attempted_at < datetime('now', '-1 hour')").rowcount
    conn.commit()
    conn.close()
    if deleted:
        logger.info(f"Cleaned {deleted} expired sessions")
    if old_attempts:
        logger.info(f"Cleaned {old_attempts} old login attempts")

    # Create startup backup in production
    if settings.is_production:
        try:
            from backup import create_backup
            create_backup(max_backups=5)
        except Exception as e:
            logger.warning(f"Startup backup failed: {e}")

    # Debug: log frontend directory and files for deployment troubleshooting
    logger.info(f"FRONTEND_DIR: {FRONTEND_DIR}")
    logger.info(f"FRONTEND_DIR exists: {os.path.exists(FRONTEND_DIR)}")
    if os.path.exists(FRONTEND_DIR):
        files = os.listdir(FRONTEND_DIR)
        logger.info(f"Frontend files: {files}")

    logger.info(f"Server ready (env={settings.ENVIRONMENT})")
    yield
    # Shutdown
    logger.info("Shutting down")


app = FastAPI(
    title="Logistics SOP Reference App",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url=None,
)

# ── Middleware ──
app.add_middleware(SecurityHeadersMiddleware)

# CORS
if settings.ALLOWED_ORIGINS == ["*"]:
    origins = ["*"]
else:
    origins = settings.ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_headers=["Content-Type", "X-Session-Token"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)

# ── API Routes ──
app.include_router(auth.router)
app.include_router(driver.router)
app.include_router(admin.router)
app.include_router(schema.router)


# ── Frontend Routes ──

@app.get("/")
async def serve_admin():
    return FileResponse(os.path.join(FRONTEND_DIR, "admin.html"))


@app.get("/driver")
async def serve_driver():
    return FileResponse(os.path.join(FRONTEND_DIR, "driver.html"))


@app.get("/install")
async def serve_install():
    path = os.path.join(FRONTEND_DIR, "install.html")
    logger.info(f"Serving /install - path={path}, exists={os.path.exists(path)}")
    if os.path.exists(path):
        return FileResponse(path)
    # Fallback: if install.html is missing, log it and return error
    logger.error(f"install.html not found at {path}")
    return JSONResponse({"error": "Install page not found", "path": path, "frontend_dir_files": os.listdir(FRONTEND_DIR) if os.path.exists(FRONTEND_DIR) else "DIR NOT FOUND"}, status_code=404)


@app.get("/manifest.json")
async def serve_manifest():
    path = os.path.join(FRONTEND_DIR, "manifest.json")
    if os.path.exists(path):
        return FileResponse(path, media_type="application/manifest+json")
    return JSONResponse({"error": "Not found"}, status_code=404)


@app.get("/sw.js")
async def serve_sw():
    path = os.path.join(FRONTEND_DIR, "sw.js")
    if os.path.exists(path):
        return FileResponse(path, media_type="application/javascript")
    return JSONResponse({"error": "Not found"}, status_code=404)


@app.get("/icons/{filename}")
async def serve_icon(filename: str):
    path = os.path.join(FRONTEND_DIR, "icons", filename)
    if os.path.exists(path):
        media = "image/svg+xml" if filename.endswith(".svg") else "image/png"
        return FileResponse(path, media_type=media)
    return JSONResponse({"error": "Not found"}, status_code=404)


@app.get("/debug/files")
async def debug_files():
    """Temporary debug endpoint to check frontend files on server."""
    result = {
        "frontend_dir": FRONTEND_DIR,
        "exists": os.path.exists(FRONTEND_DIR),
        "cwd": os.getcwd(),
        "app_file": os.path.abspath(__file__),
    }
    if os.path.exists(FRONTEND_DIR):
        result["files"] = os.listdir(FRONTEND_DIR)
        icons_dir = os.path.join(FRONTEND_DIR, "icons")
        if os.path.exists(icons_dir):
            result["icons"] = os.listdir(icons_dir)
    return result


@app.get("/health")
async def health_check():
    from database import get_db
    uptime_seconds = int(time.time() - _start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    try:
        conn = get_db()
        conn.execute("SELECT 1")
        counts = {
            "customers": conn.execute("SELECT COUNT(*) FROM customers WHERE is_active=1").fetchone()[0],
            "drivers": conn.execute("SELECT COUNT(*) FROM drivers WHERE is_active=1").fetchone()[0],
            "active_sessions": conn.execute("SELECT COUNT(*) FROM sessions WHERE expires_at > datetime('now')").fetchone()[0],
        }
        conn.close()
        return {
            "status": "ok",
            "db": "connected",
            "uptime": f"{hours}h {minutes}m {seconds}s",
            "uptime_seconds": uptime_seconds,
            "environment": settings.ENVIRONMENT,
            "counts": counts,
        }
    except Exception as e:
        return JSONResponse({"status": "error", "db": str(e)}, status_code=503)


@app.post("/api/admin/backup")
async def trigger_backup(request: Request):
    from middleware.auth import require_admin
    session = require_admin(request)  # raises 401/403 if not admin
    from backup import create_backup, list_backups
    path = create_backup()
    if path:
        return {"message": "Backup created", "backups": list_backups()}
    return JSONResponse({"error": "Backup failed"}, status_code=500)
