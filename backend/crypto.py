"""
SOP App - Field-level encryption for sensitive data.
Uses Fernet (AES-128-CBC with HMAC) for encrypting sensitive SOP fields like gate codes.
"""
import base64
import os

from cryptography.fernet import Fernet, InvalidToken

from config import settings
from database import SENSITIVE_FIELDS

# Build or derive a Fernet key from the ENCRYPTION_KEY env var.
# If no key is set, generate one and warn (dev mode only).
_fernet: Fernet | None = None


def _get_fernet() -> Fernet | None:
    global _fernet
    if _fernet is not None:
        return _fernet

    key = settings.ENCRYPTION_KEY
    if not key:
        if settings.is_production:
            raise RuntimeError("ENCRYPTION_KEY environment variable is required in production")
        # Dev mode: no encryption, return None
        return None

    # Accept either a raw Fernet key (44 chars base64) or an arbitrary string
    if len(key) == 44:
        try:
            _fernet = Fernet(key.encode())
            return _fernet
        except Exception:
            pass

    # Derive a Fernet-compatible key from arbitrary string
    import hashlib
    derived = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())
    _fernet = Fernet(derived)
    return _fernet


def encrypt_value(value: str) -> str:
    f = _get_fernet()
    if f is None:
        return value  # no encryption in dev without key
    return f.encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    f = _get_fernet()
    if f is None:
        return value
    try:
        return f.decrypt(value.encode()).decode()
    except InvalidToken:
        # Value may not be encrypted (pre-migration data)
        return value


def encrypt_if_sensitive(requirement_key: str, value: str) -> str:
    if requirement_key in SENSITIVE_FIELDS:
        return encrypt_value(value)
    return value


def decrypt_if_sensitive(requirement_key: str, value: str) -> str:
    if requirement_key in SENSITIVE_FIELDS:
        return decrypt_value(value)
    return value
