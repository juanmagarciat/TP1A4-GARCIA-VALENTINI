from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.libros.models import LibroAutor


class Autor(SQLModel, table=True):
    __tablename__ = "autor"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=255, nullable=False)
    nacionalidad: str = Field(max_length=100, nullable=False)

    autorias: List["LibroAutor"] = Relationship(back_populates="autor")
