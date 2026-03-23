"""
SOP Reference App - Startup Script
Run: python run.py

Requirements: Python 3.10+ with dependencies from requirements.txt
Render/cloud: Set PORT env var (defaults to 8000)
"""
import sys
import os
import logging

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("sop_app")

logger.info("=" * 50)
logger.info("  LOGISTICS SOP REFERENCE APP - Starting Up")
logger.info("=" * 50)

# Run migrations
logger.info("[1/3] Running database migrations...")
from migrations import run_migrations
run_migrations()

# Initialize database and seed data
logger.info("[2/3] Initializing database and seeding data...")
from seed_data import seed
seed()

# Start server with uvicorn
logger.info("[3/3] Starting FastAPI server...")
port = int(os.environ.get("PORT", 8000))

import uvicorn
uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False, log_level="info")
