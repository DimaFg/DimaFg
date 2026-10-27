import hashlib
import hmac

from app.core.config import get_settings


def hmac_digest(value: str, purpose: str) -> str:
    """Обезличенный стабильный отпечаток (например, IP для rate limit)."""
    key = f"{get_settings().app_secret}:{purpose}".encode()
    return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()
