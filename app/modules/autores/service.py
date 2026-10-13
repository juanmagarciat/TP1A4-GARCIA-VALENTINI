from typing import List

from app.core.errors import get_integrity_http_exception
from app.modules.autores.models import Autor
from app.modules.autores.schemas import AutorCreate, AutorUpdate
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select


async def create_autor(session: AsyncSession, data: AutorCreate) -> Autor:
    autor = Autor.model_validate(data)
    session.add(autor)
    try:
        await session.flush()
        await session.refresh(autor)
        return autor
    except IntegrityError as exc:
        raise get_integrity_http_exception(exc)


async def list_autores(
    session: AsyncSession, offset: int = 0, limit: int = 20
) -> List[Autor]:
    stmt = select(Autor).offset(offset).limit(limit).order_by(Autor.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_autor_by_id(session: AsyncSession, autor_id: int) -> Autor:
    autor = await session.get(Autor, autor_id)
    if not autor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Autor no encontrado.",
        )
    return autor


async def update_autor(
    session: AsyncSession, autor_id: int, data: AutorUpdate
) -> Autor:
    autor = await get_autor_by_id(session, autor_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(autor, key, value)
    try:
        session.add(autor)
        await session.flush()
        await session.refresh(autor)
        return autor
    except IntegrityError as exc:
        raise get_integrity_http_exception(exc)


async def list_libros_autor(
    session: AsyncSession, autor_id: int, offset: int, limit: int
):
    from app.modules.autores.schemas import LibroDeAutorRead
    from app.modules.libros.models import LibroAutor
    from sqlalchemy.orm import joinedload

    await get_autor_by_id(session, autor_id)
    stmt = (
        select(LibroAutor)
        .where(LibroAutor.autor_id == autor_id)
        .options(joinedload(LibroAutor.libro))
        .order_by(LibroAutor.libro_id)
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return [
        LibroDeAutorRead(
            libro_id=a.libro_id,
            titulo=a.libro.titulo,
            isbn=a.libro.isbn,
            precio=a.libro.precio,
            rol=a.rol,
            orden=a.orden,
        )
        for a in result.scalars()
    ]
