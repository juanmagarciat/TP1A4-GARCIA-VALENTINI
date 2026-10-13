from typing import List

from app.core.errors import get_integrity_http_exception
from app.modules.editoriales.models import Editorial
from app.modules.editoriales.schemas import EditorialCreate, EditorialUpdate
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select


async def create_editorial(session: AsyncSession, data: EditorialCreate) -> Editorial:
    editorial = Editorial.model_validate(data)
    session.add(editorial)
    try:
        await session.flush()
        await session.refresh(editorial)
        return editorial
    except IntegrityError as exc:
        raise get_integrity_http_exception(exc)


async def list_editoriales(
    session: AsyncSession, offset: int = 0, limit: int = 20
) -> List[Editorial]:
    stmt = select(Editorial).offset(offset).limit(limit).order_by(Editorial.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_editorial_by_id(session: AsyncSession, editorial_id: int) -> Editorial:
    editorial = await session.get(Editorial, editorial_id)
    if not editorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Editorial no encontrada.",
        )
    return editorial


async def update_editorial(
    session: AsyncSession, editorial_id: int, data: EditorialUpdate
) -> Editorial:
    editorial = await get_editorial_by_id(session, editorial_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(editorial, key, value)
    try:
        session.add(editorial)
        await session.flush()
        await session.refresh(editorial)
        return editorial
    except IntegrityError as exc:
        raise get_integrity_http_exception(exc)
