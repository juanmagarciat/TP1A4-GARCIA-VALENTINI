from typing import List

from app.core.database import get_session
from app.modules.autores import service
from app.modules.autores.schemas import (
    AutorCreate,
    AutorRead,
    AutorUpdate,
    LibroDeAutorRead,
)
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/autores", tags=["Autores"])


@router.post("/", response_model=AutorRead, status_code=status.HTTP_201_CREATED)
async def create_autor(
    payload: AutorCreate,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.create_autor(session, payload)


@router.get("/", response_model=List[AutorRead], status_code=status.HTTP_200_OK)
async def list_autores(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.list_autores(session, offset=offset, limit=limit)


@router.get("/{id}", response_model=AutorRead, status_code=status.HTTP_200_OK)
async def get_autor(
    id: int,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.get_autor_by_id(session, id)


@router.patch("/{id}", response_model=AutorRead, status_code=status.HTTP_200_OK)
async def update_autor(
    id: int,
    payload: AutorUpdate,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.update_autor(session, id, payload)


@router.get("/{id}/libros", response_model=List[LibroDeAutorRead])
async def libros_del_autor(
    id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.list_libros_autor(session, id, offset, limit)
