from decimal import Decimal
from typing import Optional

from app.core.contracts import Contract, PartialUpdate
from sqlmodel import Field


class AutorBase(Contract):
    nombre: str = Field(min_length=1, max_length=255)
    nacionalidad: str = Field(min_length=1, max_length=100)


class AutorCreate(AutorBase):
    pass


class AutorRead(AutorBase):
    id: int


class AutorUpdate(PartialUpdate):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=255)
    nacionalidad: Optional[str] = Field(default=None, min_length=1, max_length=100)


class LibroDeAutorRead(Contract):
    libro_id: int
    titulo: str
    isbn: str
    precio: Decimal
    rol: str
    orden: int
