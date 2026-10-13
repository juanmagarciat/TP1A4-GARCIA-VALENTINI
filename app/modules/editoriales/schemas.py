from typing import Optional

from app.core.contracts import Contract, PartialUpdate
from sqlmodel import Field


class EditorialBase(Contract):
    nombre: str = Field(min_length=1, max_length=255)
    pais: str = Field(min_length=1, max_length=100)


class EditorialCreate(EditorialBase):
    pass


class EditorialRead(EditorialBase):
    id: int


class EditorialUpdate(PartialUpdate):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=255)
    pais: Optional[str] = Field(default=None, min_length=1, max_length=100)
