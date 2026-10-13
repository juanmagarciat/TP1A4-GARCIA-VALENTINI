"""Carga reproducible. --reset borra SOLO los datos de la base DATABASE_URL."""

import argparse
import asyncio
from decimal import Decimal

import app.modules.ventas.models  # noqa: F401 - registra Venta y RenglonVenta
from app.core.config import settings
from app.modules.autores.models import Autor
from app.modules.clientes.models import Cliente
from app.modules.editoriales.models import Editorial
from app.modules.generos.models import Genero
from app.modules.libros.models import Libro, LibroAutor
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


async def seed(reset=False):
    engine = create_async_engine(settings.DATABASE_URL)
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            async with session.begin():
                if reset:
                    await session.execute(
                        text(
                            "TRUNCATE renglon_venta, venta, perfil_cliente, cliente, libro_autor, libro, autor, genero, editorial RESTART IDENTITY CASCADE"
                        )
                    )
                elif (
                    await session.execute(
                        text("SELECT EXISTS (SELECT 1 FROM editorial)")
                    )
                ).scalar():
                    raise RuntimeError(
                        "La base ya tiene datos. Usar --reset únicamente en una base de prueba."
                    )
                e = Editorial(nombre="Sudamericana", pais="Argentina")
                g = Genero(nombre="Novela")
                a = Autor(nombre="Julio Cortázar", nacionalidad="Argentina")
                b = Autor(nombre="Silvina Ocampo", nacionalidad="Argentina")
                c = Cliente(nombre="Cliente de prueba", email="cliente@example.com")
                session.add_all([e, g, a, b, c])
                await session.flush()
                uno = Libro(
                    isbn="978-950-00-0001-1",
                    titulo="Rayuela",
                    precio=Decimal("25000.00"),
                    stock=20,
                    editorial_id=e.id,
                    genero_id=g.id,
                )
                dos = Libro(
                    isbn="978-950-00-0002-2",
                    titulo="Antología de prueba",
                    precio=Decimal("21000.00"),
                    stock=20,
                    editorial_id=e.id,
                    genero_id=g.id,
                )
                uno.autorias = [LibroAutor(autor_id=a.id, rol="autor", orden=1)]
                dos.autorias = [
                    LibroAutor(autor_id=a.id, rol="coautor", orden=1),
                    LibroAutor(autor_id=b.id, rol="coautor", orden=2),
                ]
                session.add_all([uno, dos])
                await session.flush()
                return {
                    "editorial": e.id,
                    "genero": g.id,
                    "autor": a.id,
                    "cliente": c.id,
                    "libros": [uno.id, dos.id],
                }
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Borra los datos de DATABASE_URL y reinicia los IDs",
    )
    args = parser.parse_args()
    print(asyncio.run(seed(args.reset)))
