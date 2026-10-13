from typing import List

from app.core.errors import get_integrity_http_exception
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteUpdate,
    PerfilClienteCreate,
    PerfilClienteUpdate,
)
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select


async def create_cliente(session: AsyncSession, data: ClienteCreate) -> Cliente:
    cliente = Cliente.model_validate(data)
    session.add(cliente)
    try:
        await session.flush()
        await session.refresh(cliente)
        return cliente
    except IntegrityError as exc:
        raise get_integrity_http_exception(exc)


async def list_clientes(
    session: AsyncSession, offset: int = 0, limit: int = 20
) -> List[Cliente]:
    stmt = (
        select(Cliente)
        .options(joinedload(Cliente.perfil))
        .offset(offset)
        .limit(limit)
        .order_by(Cliente.id)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_cliente_by_id(session: AsyncSession, cliente_id: int) -> Cliente:
    stmt = (
        select(Cliente)
        .where(Cliente.id == cliente_id)
        .options(joinedload(Cliente.perfil))
    )
    result = await session.execute(stmt)
    cliente = result.scalars().first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado.",
        )
    return cliente


async def update_cliente(
    session: AsyncSession, cliente_id: int, data: ClienteUpdate
) -> Cliente:
    cliente = await get_cliente_by_id(session, cliente_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cliente, key, value)
    try:
        session.add(cliente)
        await session.flush()
        return await get_cliente_by_id(session, cliente_id)
    except IntegrityError as exc:
        raise get_integrity_http_exception(exc)


async def create_perfil(
    session: AsyncSession, cliente_id: int, data: PerfilClienteCreate
) -> PerfilCliente:
    """
    Cumple RN-09: Un cliente solo puede tener un perfil.
    Si ya tiene perfil, responde 409 Conflict.
    """
    await get_cliente_by_id(session, cliente_id)
    perfil = PerfilCliente(
        cliente_id=cliente_id,
        telefono=data.telefono,
        direccion=data.direccion,
    )
    try:
        session.add(perfil)
        await session.flush()
        await session.refresh(perfil)
        return perfil
    except IntegrityError as exc:
        raise get_integrity_http_exception(exc)


async def get_perfil(session: AsyncSession, cliente_id: int) -> PerfilCliente:
    cliente = await get_cliente_by_id(session, cliente_id)
    if not cliente.perfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El cliente no posee un perfil configurado.",
        )
    return cliente.perfil


async def update_perfil(
    session: AsyncSession, cliente_id: int, data: PerfilClienteUpdate
) -> PerfilCliente:
    perfil = await get_perfil(session, cliente_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(perfil, key, value)
    try:
        session.add(perfil)
        await session.flush()
        await session.refresh(perfil)
        return perfil
    except IntegrityError as exc:
        raise get_integrity_http_exception(exc)
