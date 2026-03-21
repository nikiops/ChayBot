from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.favorite import FavoriteItemOut, FavoriteToggleIn
from app.services.catalog import get_product_by_id
from app.services.favorites import list_favorites, toggle_favorite

router = APIRouter()


@router.get("", response_model=list[FavoriteItemOut])
async def get_favorites(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    return await list_favorites(session, current_user.id)


@router.post("/toggle")
async def toggle_favorite_item(
    payload: FavoriteToggleIn,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, bool]:
    product = await get_product_by_id(session, payload.product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден.")
    is_favorite = await toggle_favorite(session, current_user.id, payload.product_id)
    return {"is_favorite": is_favorite}

