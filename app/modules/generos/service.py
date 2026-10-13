from typing import List

from app.core.errors import get_integrity_http_exception
from app.modules.generos.models import Genero
from app.modules.generos.schemas import GeneroCreate, GeneroUpdate
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select


async def create_genero(session: AsyncSession, data: GeneroCreate) -> Genero:
    genero = Genero.model_validate(data)
    session.add(genero)
    try:
        await session.flush()
        await session.refresh(genero)
        return genero
    except IntegrityError as exc:
        raise get_integrity_http_exception(exc)


async def list_generos(
    session: AsyncSession, offset: int = 0, limit: int = 20
) -> List[Genero]:
    stmt = select(Genero).offset(offset).limit(limit).order_by(Genero.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_genero_by_id(session: AsyncSession, genero_id: int) -> Genero:
    genero = await session.get(Genero, genero_id)
    if not genero:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Género no encontrado.",
        )
    return genero


async def update_genero(
    session: AsyncSession, genero_id: int, data: GeneroUpdate
) -> Genero:
    genero = await get_genero_by_id(session, genero_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(genero, key, value)
    try:
        session.add(genero)
        await session.flush()
        await session.refresh(genero)
        return genero
    except IntegrityError as exc:
        raise get_integrity_http_exception(exc)
