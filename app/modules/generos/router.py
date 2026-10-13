from typing import List

from app.core.database import get_session
from app.modules.generos import service
from app.modules.generos.schemas import GeneroCreate, GeneroRead, GeneroUpdate
from app.modules.libros.schemas import LibroDetailRead
from app.modules.libros.service import list_libros
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/generos", tags=["Géneros"])


@router.post("/", response_model=GeneroRead, status_code=status.HTTP_201_CREATED)
async def create_genero(
    payload: GeneroCreate,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.create_genero(session, payload)


@router.get("/", response_model=List[GeneroRead], status_code=status.HTTP_200_OK)
async def list_generos(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.list_generos(session, offset=offset, limit=limit)


@router.get("/{id}", response_model=GeneroRead, status_code=status.HTTP_200_OK)
async def get_genero(
    id: int,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.get_genero_by_id(session, id)


@router.patch("/{id}", response_model=GeneroRead, status_code=status.HTTP_200_OK)
async def update_genero(
    id: int,
    payload: GeneroUpdate,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.update_genero(session, id, payload)


@router.get("/{id}/libros", response_model=List[LibroDetailRead])
async def libros_relacionados(
    id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session, scope="function"),
):
    await service.get_genero_by_id(session, id)
    return await list_libros(session, offset=offset, limit=limit, genero_id=id)
