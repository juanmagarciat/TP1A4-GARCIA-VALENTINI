from typing import Optional

from app.core.contracts import Contract, PartialUpdate
from sqlmodel import Field


class GeneroBase(Contract):
    nombre: str = Field(min_length=1, max_length=100)


class GeneroCreate(GeneroBase):
    pass


class GeneroRead(GeneroBase):
    id: int


class GeneroUpdate(PartialUpdate):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100)
