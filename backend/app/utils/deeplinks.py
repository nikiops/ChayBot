from urllib.parse import quote


def _sanitize_bot_username(bot_username: str) -> str:
    return bot_username.strip().lstrip("@")


def build_start_link(bot_username: str, payload: str | None = None) -> str:
    username = _sanitize_bot_username(bot_username)
    base = f"https://t.me/{username}"
    return f"{base}?start={quote(payload)}" if payload else base


def build_startapp_link(bot_username: str, payload: str | None = None, mode: str = "compact") -> str:
    username = _sanitize_bot_username(bot_username)
    base = f"https://t.me/{username}?startapp"
    if payload:
        return f"{base}={quote(payload)}&mode={mode}"
    return f"{base}&mode={mode}"
