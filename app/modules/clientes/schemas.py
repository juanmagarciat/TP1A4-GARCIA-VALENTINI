from typing import Optional

from app.core.contracts import Contract, PartialUpdate
from pydantic import EmailStr
from sqlmodel import Field


class PerfilClienteBase(Contract):
    telefono: str = Field(min_length=1, max_length=50)
    direccion: str = Field(min_length=1, max_length=255)


class PerfilClienteCreate(PerfilClienteBase):
    pass


class PerfilClienteUpdate(PartialUpdate):
    telefono: Optional[str] = Field(default=None, min_length=1, max_length=50)
    direccion: Optional[str] = Field(default=None, min_length=1, max_length=255)


class PerfilClienteRead(PerfilClienteBase):
    id: int
    cliente_id: int


class ClienteBase(Contract):
    nombre: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(max_length=255)


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(PartialUpdate):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[EmailStr] = Field(default=None, max_length=255)


class ClienteRead(ClienteBase):
    id: int


class ClienteDetailRead(ClienteRead):
    perfil: Optional[PerfilClienteRead] = None
