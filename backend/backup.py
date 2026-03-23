"""
SOP App - SQLite Backup Utility
Creates timestamped backups of the database file.
Can be run standalone or called from the app.
"""
import os
import shutil
import logging
from datetime import datetime

from config import settings

logger = logging.getLogger(__name__)

BACKUP_DIR = os.path.join(os.path.dirname(settings.DB_PATH), "backups")


def create_backup(max_backups: int = 10) -> str | None:
    """Create a timestamped backup of the SQLite database.
    Returns the backup file path, or None if backup failed.
    Keeps at most max_backups files, removing oldest.
    """
    if not os.path.exists(settings.DB_PATH):
        logger.warning("No database file to backup")
        return None

    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"sop_app_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    try:
        # Use SQLite's backup API for a consistent copy
        import sqlite3
        source = sqlite3.connect(settings.DB_PATH)
        dest = sqlite3.connect(backup_path)
        source.backup(dest)
        dest.close()
        source.close()
        logger.info(f"Backup created: {backup_path}")
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        # Fallback to file copy
        try:
            shutil.copy2(settings.DB_PATH, backup_path)
            logger.info(f"Backup created (file copy): {backup_path}")
        except Exception as e2:
            logger.error(f"Backup file copy also failed: {e2}")
            return None

    # Rotate old backups
    _rotate_backups(max_backups)
    return backup_path


def _rotate_backups(max_backups: int):
    """Remove oldest backups if we exceed max_backups."""
    if not os.path.exists(BACKUP_DIR):
        return
    backups = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.startswith("sop_app_") and f.endswith(".db")],
        key=lambda f: os.path.getmtime(os.path.join(BACKUP_DIR, f))
    )
    while len(backups) > max_backups:
        oldest = backups.pop(0)
        os.remove(os.path.join(BACKUP_DIR, oldest))
        logger.info(f"Removed old backup: {oldest}")


def list_backups() -> list[dict]:
    """List all available backups with metadata."""
    if not os.path.exists(BACKUP_DIR):
        return []
    backups = []
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if f.startswith("sop_app_") and f.endswith(".db"):
            path = os.path.join(BACKUP_DIR, f)
            backups.append({
                "filename": f,
                "size_mb": round(os.path.getsize(path) / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(os.path.getmtime(path)).isoformat(),
            })
    return backups


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    path = create_backup()
    if path:
        print(f"Backup: {path}")
    print(f"All backups: {list_backups()}")
