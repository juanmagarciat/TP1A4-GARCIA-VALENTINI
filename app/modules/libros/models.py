from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import CheckConstraint, Column, Integer, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.autores.models import Autor
    from app.modules.editoriales.models import Editorial
    from app.modules.generos.models import Genero
    from app.modules.ventas.models import RenglonVenta


class LibroAutor(SQLModel, table=True):
    __tablename__ = "libro_autor"
    __table_args__ = (
        CheckConstraint(
            "rol IN ('autor', 'coautor', 'traductor', 'ilustrador')",
            name="chk_libro_autor_rol",
        ),
        CheckConstraint("orden >= 1", name="chk_libro_autor_orden"),
    )

    libro_id: int = Field(
        foreign_key="libro.id",
        ondelete="CASCADE",
        primary_key=True,
        index=True,
    )
    autor_id: int = Field(
        foreign_key="autor.id",
        primary_key=True,
        index=True,
    )
    rol: str = Field(max_length=50, default="autor", nullable=False)
    orden: int = Field(default=1, nullable=False)

    libro: Optional["Libro"] = Relationship(back_populates="autorias")
    autor: Optional["Autor"] = Relationship(back_populates="autorias")


class Libro(SQLModel, table=True):
    __tablename__ = "libro"
    __table_args__ = (
        CheckConstraint("precio > 0", name="chk_libro_precio_positivo"),
        CheckConstraint("stock >= 0", name="chk_libro_stock_no_negativo"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    isbn: str = Field(
        max_length=50, sa_column_kwargs={"unique": True}, index=True, nullable=False
    )
    titulo: str = Field(max_length=255, index=True, nullable=False)
    precio: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    stock: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    editorial_id: int = Field(foreign_key="editorial.id", index=True, nullable=False)
    genero_id: Optional[int] = Field(
        default=None,
        foreign_key="genero.id",
        index=True,
        nullable=True,
    )

    editorial: Optional["Editorial"] = Relationship(back_populates="libros")
    genero: Optional["Genero"] = Relationship(back_populates="libros")
    autorias: List[LibroAutor] = Relationship(
        back_populates="libro",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "order_by": "LibroAutor.orden, LibroAutor.autor_id",
        },
    )
    renglones_venta: List["RenglonVenta"] = Relationship(back_populates="libro")
