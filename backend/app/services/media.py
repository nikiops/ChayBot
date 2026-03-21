from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import Settings

MAX_PRODUCT_IMAGE_SIZE_BYTES = 6 * 1024 * 1024
PRODUCT_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _normalize_extension(upload: UploadFile) -> str:
    filename = upload.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    return PRODUCT_IMAGE_CONTENT_TYPES.get(upload.content_type or "", ".jpg")


async def store_product_image(upload: UploadFile, settings: Settings) -> dict[str, str | int]:
    if upload.content_type not in PRODUCT_IMAGE_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Загрузите фото в формате JPG, PNG или WEBP.",
        )

    payload = await upload.read()
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Файл изображения не загружен.")
    if len(payload) > MAX_PRODUCT_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Фото слишком большое. Максимум 6 МБ.")

    extension = _normalize_extension(upload)
    file_name = f"{uuid4().hex}{extension}"
    target_dir = Path(settings.media_dir) / "products"
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / file_name
    file_path.write_bytes(payload)

    return {
        "image_url": f"/media/products/{file_name}",
        "file_name": file_name,
        "content_type": upload.content_type or "image/jpeg",
        "size_bytes": len(payload),
    }


def resolve_media_path(settings: Settings, media_url: str | None) -> Path | None:
    if not media_url:
        return None

    parts = list(Path(media_url.lstrip("/")).parts)
    if not parts:
        return None
    if parts[0] == "media":
        parts = parts[1:]
    if not parts:
        return None

    file_path = Path(settings.media_dir).joinpath(*parts)
    if file_path.exists():
        return file_path
    return None
