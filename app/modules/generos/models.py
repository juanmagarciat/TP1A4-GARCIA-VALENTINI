from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.libros.models import Libro


class Genero(SQLModel, table=True):
    __tablename__ = "genero"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(
        max_length=255, sa_column_kwargs={"unique": True}, index=True, nullable=False
    )

    libros: List["Libro"] = Relationship(back_populates="genero")
