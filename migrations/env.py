import asyncio
from logging.config import fileConfig

import app.modules.autores.models  # noqa: F401
import app.modules.clientes.models  # noqa: F401

# Importar todos los modelos para que SQLModel.metadata tenga registrado el esquema completo
import app.modules.editoriales.models  # noqa: F401
import app.modules.generos.models  # noqa: F401
import app.modules.libros.models  # noqa: F401
import app.modules.ventas.models  # noqa: F401
from alembic import context
from app.core.config import settings
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = config.attributes.get("target_metadata", SQLModel.metadata)


def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo 'offline'."""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Configura y ejecuta el motor asincrónico para migraciones online."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Ejecuta migraciones en modo 'online' usando asyncio."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
