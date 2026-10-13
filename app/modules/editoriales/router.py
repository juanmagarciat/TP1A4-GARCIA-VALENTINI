from typing import List

from app.core.database import get_session
from app.modules.editoriales import service
from app.modules.editoriales.schemas import (
    EditorialCreate,
    EditorialRead,
    EditorialUpdate,
)
from app.modules.libros.schemas import LibroDetailRead
from app.modules.libros.service import list_libros
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/editoriales", tags=["Editoriales"])


@router.post("/", response_model=EditorialRead, status_code=status.HTTP_201_CREATED)
async def create_editorial(
    payload: EditorialCreate,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.create_editorial(session, payload)


@router.get("/", response_model=List[EditorialRead], status_code=status.HTTP_200_OK)
async def list_editoriales(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.list_editoriales(session, offset=offset, limit=limit)


@router.get("/{id}", response_model=EditorialRead, status_code=status.HTTP_200_OK)
async def get_editorial(
    id: int,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.get_editorial_by_id(session, id)


@router.patch("/{id}", response_model=EditorialRead, status_code=status.HTTP_200_OK)
async def update_editorial(
    id: int,
    payload: EditorialUpdate,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.update_editorial(session, id, payload)


@router.get("/{id}/libros", response_model=List[LibroDetailRead])
async def libros_relacionados(
    id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session, scope="function"),
):
    await service.get_editorial_by_id(session, id)
    return await list_libros(session, offset=offset, limit=limit, editorial_id=id)
