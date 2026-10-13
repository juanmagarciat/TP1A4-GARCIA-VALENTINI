from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from app.core.contracts import Contract
from app.modules.clientes.schemas import ClienteRead
from pydantic import field_validator
from sqlmodel import Field


class RenglonCreate(Contract):
    libro_id: int = Field(gt=0, le=2147483647)
    cantidad: int = Field(gt=0, le=2147483647)


class VentaCreate(Contract):
    cliente_id: int = Field(gt=0, le=2147483647)
    renglones: List[RenglonCreate]

    @field_validator("renglones")
    @classmethod
    def validate_renglones(cls, v: List[RenglonCreate]) -> List[RenglonCreate]:
        if not v or len(v) == 0:
            raise ValueError("La venta debe contener al menos un renglón.")
        libro_ids = [r.libro_id for r in v]
        if len(libro_ids) != len(set(libro_ids)):
            raise ValueError(
                "No se permiten libros duplicados en los renglones de la venta."
            )
        return v


class RenglonRead(Contract):
    id: int
    venta_id: int
    libro_id: int
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
    titulo: str


class VentaRead(Contract):
    id: int
    cliente_id: int
    fecha: datetime
    total: Decimal
    cliente: Optional[ClienteRead] = None
    renglones: List[RenglonRead] = Field(default_factory=list)
