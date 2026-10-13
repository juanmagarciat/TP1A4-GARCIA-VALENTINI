from typing import List, Optional

from app.core.errors import get_integrity_http_exception
from app.modules.libros.models import Libro, LibroAutor
from app.modules.libros.schemas import LibroCreate, LibroUpdate
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import col, select


async def create_libro(session: AsyncSession, data: LibroCreate) -> Libro:
    """
    Crea un libro y sus autorías asociadas.
    Cumple RN-12: no valida con 'if' previos la existencia de editorial_id o autor_id;
    escribe directamente y deja que PostgreSQL dispare la violación de clave foránea (409).
    """
    libro = Libro(
        isbn=data.isbn,
        titulo=data.titulo,
        precio=data.precio,
        stock=data.stock,
        editorial_id=data.editorial_id,
        genero_id=data.genero_id,
    )
    try:
        session.add(libro)
        await session.flush()

        for a in data.autores:
            autoria = LibroAutor(
                libro_id=libro.id,
                autor_id=a.autor_id,
                rol=a.rol,
                orden=a.orden,
            )
            session.add(autoria)

        await session.flush()
        return await get_libro_by_id(session, libro.id)
    except IntegrityError as exc:
        raise get_integrity_http_exception(exc)


async def get_libro_by_id(session: AsyncSession, libro_id: int) -> Libro:
    """
    Obtiene un libro por su ID con carga anticipada (eager loading) para evitar N+1:
    - joinedload para editorial y género (relaciones a uno).
    - selectinload para autorias y joinedload para autor (colección y su relación).
    Ejecución en número fijo y constante de consultas.
    """
    stmt = (
        select(Libro)
        .where(Libro.id == libro_id)
        .execution_options(populate_existing=True)
        .options(
            joinedload(Libro.editorial),
            joinedload(Libro.genero),
            selectinload(Libro.autorias).joinedload(LibroAutor.autor),
        )
    )
    result = await session.execute(stmt)
    libro = result.scalars().first()
    if not libro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libro no encontrado.",
        )
    return libro


async def list_libros(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 20,
    titulo: Optional[str] = None,
    genero_id: Optional[int] = None,
    editorial_id: Optional[int] = None,
) -> List[Libro]:
    """
    Lista libros con paginación y búsqueda insensible a mayúsculas/minúsculas.
    Cumple RN-11: utiliza parámetros ligados en SQLAlchemy con .ilike(), nunca concatenación SQL.
    Aplica eager loading para evitar el problema N+1.
    """
    stmt = (
        select(Libro)
        .options(
            joinedload(Libro.editorial),
            joinedload(Libro.genero),
            selectinload(Libro.autorias).joinedload(LibroAutor.autor),
        )
        .order_by(Libro.id)
    )

    if titulo:
        stmt = stmt.where(col(Libro.titulo).ilike(f"%{titulo}%"))

    if genero_id is not None:
        stmt = stmt.where(Libro.genero_id == genero_id)
    if editorial_id is not None:
        stmt = stmt.where(Libro.editorial_id == editorial_id)
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().unique().all())


async def update_libro(
    session: AsyncSession, libro_id: int, data: LibroUpdate
) -> Libro:
    libro = await get_libro_by_id(session, libro_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(libro, key, value)
    try:
        session.add(libro)
        await session.flush()
        return await get_libro_by_id(session, libro_id)
    except IntegrityError as exc:
        raise get_integrity_http_exception(exc)
