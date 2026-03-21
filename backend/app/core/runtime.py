from threading import Lock

from app.core.config import get_settings

_state_lock = Lock()
_public_webapp_url: str | None = None


def set_public_webapp_url(url: str | None) -> None:
    global _public_webapp_url
    normalized = url.rstrip("/") if url else None
    with _state_lock:
        _public_webapp_url = normalized


def get_public_webapp_url() -> str:
    with _state_lock:
        if _public_webapp_url:
            return _public_webapp_url
    return get_settings().webapp_base_url

