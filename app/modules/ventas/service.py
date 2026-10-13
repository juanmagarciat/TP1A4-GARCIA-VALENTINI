import asyncio
import logging
from decimal import Decimal
from typing import List

from app.core.errors import get_integrity_http_exception
from app.modules.clientes.models import Cliente
from app.modules.libros.models import Libro
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.schemas import RenglonRead, VentaCreate, VentaRead
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select

logger = logging.getLogger("libreria.ventas")


async def enviar_comprobante(venta_id: int, email: str) -> None:
    """
    Tarea asincrónica en segundo plano (BackgroundTasks).
    Simula el envío de un comprobante de venta por email sin bloquear el event loop.
    """
    logger.info(
        f"[COMPROBANTE] Iniciando simulación de envío de comprobante para venta #{venta_id} a '{email}'..."
    )
    await asyncio.sleep(0.5)
    logger.info(
        f"[COMPROBANTE] Comprobante para venta #{venta_id} enviado exitosamente a '{email}'."
    )


def build_venta_read(venta: Venta) -> VentaRead:
    """Convierte una entidad Venta en el esquema VentaRead calculando subtotales por renglón."""
    renglones_read = [
        RenglonRead(
            id=r.id,
            venta_id=r.venta_id,
            libro_id=r.libro_id,
            cantidad=r.cantidad,
            precio_unitario=r.precio_unitario,
            subtotal=r.precio_unitario * r.cantidad,
            titulo=r.libro.titulo,
        )
        for r in (venta.renglones or [])
    ]
    return VentaRead(
        id=venta.id,
        cliente_id=venta.cliente_id,
        fecha=venta.fecha,
        total=venta.total,
        cliente=venta.cliente,
        renglones=renglones_read,
    )


async def create_venta(
    session: AsyncSession,
    data: VentaCreate,
    background_tasks: BackgroundTasks,
) -> VentaRead:
    """
    Crea una venta con sus renglones correspondientes.
    - Valida existencia de cliente y libros (409 si no existen, cumpliendo C-05).
    - Valida disponibilidad de stock (409 si es insuficiente).
    - Congela el precio unitario actual del libro en cada renglón.
    - Descuenta el stock de cada libro vendido.
    - Calcula el total acumulado de la venta.
    - Agenda el envío del comprobante como BackgroundTask asincrónica.
    """
    cliente = await session.get(Cliente, data.cliente_id)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El cliente especificado no existe.",
        )

    total_acumulado = Decimal("0.00")
    renglones_preparados = []

    # Bloquear en orden estable evita pérdida de actualizaciones y reduce deadlocks.
    ids = sorted(item.libro_id for item in data.renglones)
    result = await session.execute(
        select(Libro).where(Libro.id.in_(ids)).order_by(Libro.id).with_for_update()
    )
    libros = {libro.id: libro for libro in result.scalars()}
    for item in data.renglones:
        libro = libros.get(item.libro_id)
        if not libro:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El libro con ID {item.libro_id} no existe.",
            )

        if libro.stock < item.cantidad:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Stock insuficiente para el libro '{libro.titulo}'. Stock disponible: {libro.stock}, solicitado: {item.cantidad}.",
            )

        # Congelar precio unitario al momento de la venta
        precio_unitario = libro.precio
        subtotal = precio_unitario * item.cantidad
        total_acumulado += subtotal
        if total_acumulado > Decimal("9999999999.99"):
            raise HTTPException(
                422, "El total supera el máximo admitido para una venta."
            )

        # Descontar stock
        libro.stock -= item.cantidad
        session.add(libro)

        renglones_preparados.append(
            {
                "libro_id": item.libro_id,
                "cantidad": item.cantidad,
                "precio_unitario": precio_unitario,
            }
        )

    venta = Venta(
        cliente_id=data.cliente_id,
        total=total_acumulado,
    )

    venta.renglones = [RenglonVenta(**prep) for prep in renglones_preparados]
    try:
        session.add(venta)
        await session.flush()
    except IntegrityError as exc:
        raise get_integrity_http_exception(exc)

    # Agendar tarea en segundo plano
    background_tasks.add_task(enviar_comprobante, venta.id, cliente.email)

    return await get_venta_by_id(session, venta.id)


async def get_venta_by_id(session: AsyncSession, venta_id: int) -> VentaRead:
    """
    Obtiene el detalle de una venta con carga anticipada (eager loading) en número fijo de consultas:
    - joinedload para cliente (relación a uno).
    - selectinload para renglones y joinedload para libro de cada renglón.
    """
    stmt = (
        select(Venta)
        .where(Venta.id == venta_id)
        .options(
            joinedload(Venta.cliente),
            selectinload(Venta.renglones).joinedload(RenglonVenta.libro),
        )
    )
    result = await session.execute(stmt)
    venta = result.scalars().first()
    if not venta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venta no encontrada.",
        )
    return build_venta_read(venta)


async def list_ventas(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 20,
    cliente_id: int | None = None,
) -> List[VentaRead]:
    """Lista ventas con paginación y carga anticipada."""
    stmt = (
        select(Venta)
        .options(
            joinedload(Venta.cliente),
            selectinload(Venta.renglones).joinedload(RenglonVenta.libro),
        )
        .offset(offset)
        .limit(limit)
        .order_by(Venta.id)
    )
    if cliente_id is not None:
        stmt = stmt.where(Venta.cliente_id == cliente_id)
    result = await session.execute(stmt)
    ventas = result.scalars().unique().all()
    return [build_venta_read(v) for v in ventas]
