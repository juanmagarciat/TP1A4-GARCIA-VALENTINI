from typing import List

from app.core.database import get_session
from app.modules.ventas import service
from app.modules.ventas.schemas import VentaCreate, VentaRead
from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/ventas", tags=["Ventas"])


@router.post("/", response_model=VentaRead, status_code=status.HTTP_201_CREATED)
async def create_venta(
    payload: VentaCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    """
    Crea una nueva venta.
    RN-04 a RN-07: Congela precios, calcula total y agenda comprobante por email en segundo plano.
    RN-08: No existe endpoint PATCH para ventas.
    """
    return await service.create_venta(session, payload, background_tasks)


@router.get("/", response_model=List[VentaRead], status_code=status.HTTP_200_OK)
async def list_ventas(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session, scope="function"),
):
    """Lista las ventas con paginación (limit y offset)."""
    return await service.list_ventas(session, offset=offset, limit=limit)


@router.get("/{id}", response_model=VentaRead, status_code=status.HTTP_200_OK)
async def get_venta(
    id: int,
    session: AsyncSession = Depends(get_session, scope="function"),
):
    """Obtiene el detalle de una venta con sus renglones y cliente en consultas fijas."""
    return await service.get_venta_by_id(session, id)
