"""
SOP App - Configuration
All settings from environment variables with sensible defaults for development.
"""
import os
import secrets


class Settings:
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "development")
    DB_PATH: str = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "sop_app.db"))
    ENCRYPTION_KEY: str = os.environ.get("ENCRYPTION_KEY", "")
    SESSION_SECRET: str = os.environ.get("SESSION_SECRET", secrets.token_hex(32))
    ALLOWED_ORIGINS: list[str] = [
        o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "*").split(",") if o.strip()
    ]
    PORT: int = int(os.environ.get("PORT", 8000))

    # Session TTL in seconds
    DRIVER_SESSION_TTL: int = 8 * 3600   # 8 hours
    ADMIN_SESSION_TTL: int = 4 * 3600    # 4 hours

    # Rate limiting
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_WINDOW_SECONDS: int = 900  # 15 minutes

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


settings = Settings()
