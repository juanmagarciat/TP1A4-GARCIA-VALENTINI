from typing import List

from app.core.database import get_session
from app.modules.clientes import service
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteDetailRead,
    ClienteRead,
    ClienteUpdate,
    PerfilClienteCreate,
    PerfilClienteRead,
    PerfilClienteUpdate,
)
from app.modules.ventas.schemas import VentaRead
from app.modules.ventas.service import list_ventas
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.post("/", response_model=ClienteRead, status_code=status.HTTP_201_CREATED)
async def create_cliente(
    payload: ClienteCreate,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.create_cliente(session, payload)


@router.get("/", response_model=List[ClienteDetailRead], status_code=status.HTTP_200_OK)
async def list_clientes(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.list_clientes(session, offset=offset, limit=limit)


@router.get("/{id}", response_model=ClienteDetailRead, status_code=status.HTTP_200_OK)
async def get_cliente(
    id: int,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.get_cliente_by_id(session, id)


@router.patch("/{id}", response_model=ClienteDetailRead, status_code=status.HTTP_200_OK)
async def update_cliente(
    id: int,
    payload: ClienteUpdate,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.update_cliente(session, id, payload)


@router.post(
    "/{id}/perfil",
    response_model=PerfilClienteRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_perfil(
    id: int,
    payload: PerfilClienteCreate,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.create_perfil(session, id, payload)


@router.get(
    "/{id}/perfil",
    response_model=PerfilClienteRead,
    status_code=status.HTTP_200_OK,
)
async def get_perfil(
    id: int,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.get_perfil(session, id)


@router.patch(
    "/{id}/perfil",
    response_model=PerfilClienteRead,
    status_code=status.HTTP_200_OK,
)
async def update_perfil(
    id: int,
    payload: PerfilClienteUpdate,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    return await service.update_perfil(session, id, payload)


@router.get("/{id}/ventas", response_model=List[VentaRead])
async def ventas_del_cliente(
    id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session, scope="function"),
):
    await service.get_cliente_by_id(session, id)
    return await list_ventas(session, offset=offset, limit=limit, cliente_id=id)
