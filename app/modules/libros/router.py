from typing import List, Optional

from app.core.database import get_session
from app.modules.libros import service
from app.modules.libros.schemas import (
    LibroCreate,
    LibroDetailRead,
    LibroUpdate,
)
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/libros", tags=["Libros"])


@router.post("/", response_model=LibroDetailRead, status_code=status.HTTP_201_CREATED)
async def create_libro(
    payload: LibroCreate,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.create_libro(session, payload)


@router.get("/", response_model=List[LibroDetailRead], status_code=status.HTTP_200_OK)
async def list_libros(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    genero_id: Optional[int] = Query(default=None, gt=0),
    titulo: Optional[str] = Query(default=None, description="Búsqueda por título"),
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.list_libros(
        session, offset=offset, limit=limit, titulo=titulo, genero_id=genero_id
    )


@router.get("/{id}", response_model=LibroDetailRead, status_code=status.HTTP_200_OK)
async def get_libro(
    id: int,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.get_libro_by_id(session, id)


@router.patch("/{id}", response_model=LibroDetailRead, status_code=status.HTTP_200_OK)
async def update_libro(
    id: int,
    payload: LibroUpdate,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.update_libro(session, id, payload)
