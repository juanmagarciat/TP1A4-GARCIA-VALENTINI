from decimal import Decimal
from typing import List, Optional

from app.core.contracts import Contract, PartialUpdate
from app.modules.autores.schemas import AutorRead
from app.modules.editoriales.schemas import EditorialRead
from app.modules.generos.schemas import GeneroRead
from pydantic import field_validator
from sqlmodel import Field

ROLES_PERMITIDOS = {"autor", "coautor", "traductor", "ilustrador"}


class LibroAutorInput(Contract):
    autor_id: int = Field(gt=0, le=2147483647)
    rol: str = Field(default="autor")
    orden: int = Field(default=1, ge=1, le=2147483647)

    @field_validator("rol")
    @classmethod
    def validate_rol(cls, v: str) -> str:
        clean_rol = v.strip().lower()
        if clean_rol not in ROLES_PERMITIDOS:
            raise ValueError(
                f"Rol no válido. Debe ser uno de: {', '.join(sorted(ROLES_PERMITIDOS))}"
            )
        return clean_rol


class LibroBase(Contract):
    isbn: str = Field(min_length=1, max_length=50)
    titulo: str = Field(min_length=1, max_length=255)
    precio: Decimal = Field(gt=Decimal("0"), decimal_places=2, max_digits=10)
    stock: int = Field(default=0, ge=0, le=2147483647)
    editorial_id: int = Field(gt=0, le=2147483647)
    genero_id: Optional[int] = Field(default=None, gt=0, le=2147483647)


class LibroCreate(LibroBase):
    autores: List[LibroAutorInput] = Field(min_length=1)


class LibroUpdate(PartialUpdate):
    isbn: Optional[str] = Field(default=None, min_length=1, max_length=50)
    titulo: Optional[str] = Field(default=None, min_length=1, max_length=255)
    precio: Optional[Decimal] = Field(
        default=None, gt=Decimal("0"), decimal_places=2, max_digits=10
    )
    stock: Optional[int] = Field(default=None, ge=0, le=2147483647)
    editorial_id: Optional[int] = Field(default=None, gt=0, le=2147483647)
    genero_id: Optional[int] = Field(default=None, gt=0, le=2147483647)


class LibroAutorRead(Contract):
    autor_id: int
    rol: str
    orden: int
    autor: Optional[AutorRead] = None


class LibroRead(LibroBase):
    id: int


class LibroDetailRead(LibroRead):
    editorial: Optional[EditorialRead] = None
    genero: Optional[GeneroRead] = None
    autorias: List[LibroAutorRead] = Field(default_factory=list)
