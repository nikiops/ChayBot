from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from pathlib import Path

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)

_ngrok_process: subprocess.Popen | None = None


def _candidate_config_paths(settings: Settings) -> list[Path]:
    candidates: list[Path] = []
    if settings.ngrok_config_path:
        candidates.append(Path(settings.ngrok_config_path))

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "Packages" / "ngrok.ngrok_1g87z0zv29zzc" / "LocalCache" / "Local" / "ngrok" / "ngrok.yml")
        candidates.append(Path(local_app_data) / "ngrok" / "ngrok.yml")

    unique_candidates: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        if path.exists():
            unique_candidates.append(path)
    return unique_candidates


def _matches_tunnel_addr(addr: str, frontend_port: int) -> bool:
    tokens = (
        f"http://localhost:{frontend_port}",
        f"localhost:{frontend_port}",
        f"http://127.0.0.1:{frontend_port}",
        f"127.0.0.1:{frontend_port}",
        f":{frontend_port}",
        str(frontend_port),
    )
    return any(token in addr for token in tokens)


async def _get_existing_tunnel_url(settings: Settings) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{settings.ngrok_api_url}/api/tunnels")
            response.raise_for_status()
    except Exception:
        return None

    tunnels = response.json().get("tunnels", [])
    for tunnel in tunnels:
        public_url = tunnel.get("public_url", "")
        addr = str(tunnel.get("config", {}).get("addr", ""))
        proto = tunnel.get("proto", "")
        if public_url.startswith("https://") and proto == "https" and _matches_tunnel_addr(addr, settings.frontend_port):
            return public_url.rstrip("/")

    for tunnel in tunnels:
        public_url = tunnel.get("public_url", "")
        if public_url.startswith("https://"):
            return public_url.rstrip("/")
    return None


def _start_ngrok_process(settings: Settings) -> subprocess.Popen | None:
    global _ngrok_process
    if _ngrok_process and _ngrok_process.poll() is None:
        return _ngrok_process

    command = [
        settings.ngrok_bin,
        "http",
        f"http://127.0.0.1:{settings.frontend_port}",
        "--log",
        "stdout",
        "--log-format",
        "json",
    ]

    config_paths = _candidate_config_paths(settings)
    if config_paths:
        command.extend(["--config", str(config_paths[0])])

    kwargs: dict = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
        "cwd": Path.cwd(),
    }
    if os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    logger.info("Starting ngrok tunnel for frontend on port %s", settings.frontend_port)
    _ngrok_process = subprocess.Popen(command, **kwargs)
    return _ngrok_process


async def ensure_public_webapp_url(settings: Settings) -> str:
    if settings.webapp_base_url.startswith("https://"):
        return settings.webapp_base_url

    if not settings.use_ngrok_for_webapp:
        return settings.webapp_base_url

    existing = await _get_existing_tunnel_url(settings)
    if existing:
        logger.info("Using existing ngrok tunnel: %s", existing)
        return existing

    _start_ngrok_process(settings)
    for _ in range(30):
        await asyncio.sleep(1)
        existing = await _get_existing_tunnel_url(settings)
        if existing:
            logger.info("Ngrok tunnel is ready: %s", existing)
            return existing

    logger.warning("Ngrok tunnel did not become ready in time, falling back to %s", settings.webapp_base_url)
    return settings.webapp_base_url
