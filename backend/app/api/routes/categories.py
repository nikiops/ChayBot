from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.category import CategoryOut, CategoryWithCount
from app.services.catalog import get_category_by_slug, list_categories

router = APIRouter()


@router.get("", response_model=list[CategoryWithCount])
async def get_categories(session: AsyncSession = Depends(get_db_session)) -> list[dict]:
    return await list_categories(session)


@router.get("/{slug}", response_model=CategoryOut)
async def get_category(slug: str, session: AsyncSession = Depends(get_db_session)):
    category = await get_category_by_slug(session, slug)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена.")
    return category

