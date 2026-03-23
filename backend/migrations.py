"""
SOP App - Database Migration System
Simple numbered SQL migrations tracked in a _migrations table.
Migrations are defined inline to keep things self-contained.
"""
import logging
from database import get_db

logger = logging.getLogger(__name__)

# Each migration is a (version, description, sql) tuple.
# Migrations run in order and are idempotent (tracked by version number).
MIGRATIONS = [
    (1, "initial schema", """
        -- Initial schema is handled by init_db() in database.py
        -- This migration exists as a baseline marker
        SELECT 1;
    """),
    (2, "add is_admin to drivers", """
        -- Handled by init_db() migration logic, baseline marker
        SELECT 1;
    """),
    (3, "add sessions and login_attempts tables", """
        -- Handled by init_db(), baseline marker
        SELECT 1;
    """),
    (4, "expand audit_log columns", """
        -- Handled by init_db() migration logic, baseline marker
        SELECT 1;
    """),
]


def run_migrations():
    """Run all pending migrations."""
    conn = get_db()

    # Create migrations tracking table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            version INTEGER PRIMARY KEY,
            description TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # Get already-applied versions
    applied = {row[0] for row in conn.execute("SELECT version FROM _migrations").fetchall()}

    pending = [(v, d, s) for v, d, s in MIGRATIONS if v not in applied]
    if not pending:
        logger.info("No pending migrations.")
        conn.close()
        return

    for version, description, sql in pending:
        logger.info(f"Applying migration {version}: {description}")
        try:
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO _migrations (version, description) VALUES (?, ?)",
                (version, description)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Migration {version} failed: {e}")
            conn.close()
            raise

    logger.info(f"Applied {len(pending)} migration(s).")
    conn.close()
