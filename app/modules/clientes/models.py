from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.ventas.models import Venta


class PerfilCliente(SQLModel, table=True):
    __tablename__ = "perfil_cliente"

    id: Optional[int] = Field(default=None, primary_key=True)
    cliente_id: int = Field(
        foreign_key="cliente.id",
        ondelete="CASCADE",
        unique=True,
        index=True,
        nullable=False,
    )
    telefono: str = Field(max_length=50, nullable=False)
    direccion: str = Field(max_length=255, nullable=False)

    cliente: Optional["Cliente"] = Relationship(back_populates="perfil")


class Cliente(SQLModel, table=True):
    __tablename__ = "cliente"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=255, nullable=False)
    email: str = Field(
        max_length=255, sa_column_kwargs={"unique": True}, index=True, nullable=False
    )

    perfil: Optional[PerfilCliente] = Relationship(
        back_populates="cliente",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )
    ventas: List["Venta"] = Relationship(back_populates="cliente")
