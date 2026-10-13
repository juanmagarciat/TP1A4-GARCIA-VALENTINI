import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.errors import parse_integrity_error_detail
from app.modules.autores.router import router as autores_router
from app.modules.clientes.router import router as clientes_router
from app.modules.editoriales.router import router as editoriales_router
from app.modules.generos.router import router as generos_router
from app.modules.health.router import router as health_router
from app.modules.libros.router import router as libros_router
from app.modules.ventas.router import router as ventas_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("libreria")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manejo del ciclo de vida de la aplicación FastAPI.
    - Inicializa el motor asincrónico SQLAlchemy con diagnóstico SQL configurable.
    - Configura la fábrica de sesiones asincrónicas en app.state.
    - En el teardown, cierra y libera limpiamente los recursos del pool de conexiones.
    """
    logger.info("Iniciando motor de base de datos asincrónico...")
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.SQL_ECHO,
    )
    session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    app.state.engine = engine
    app.state.session_factory = session_factory

    try:
        yield
    finally:
        logger.info("Cerrando motor de base de datos asincrónico...")
        await engine.dispose()


app = FastAPI(
    title="Librería API - Programación III (UTN)",
    description="API REST asincrónica para catálogo, clientes y ventas con FastAPI y PostgreSQL",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """
    Manejador global para violaciones de integridad en la base de datos (RN-12).
    Traduce a HTTP 409 Conflict con mensaje amigable sin filtrar tablas ni trazas internas.
    """
    detail = parse_integrity_error_detail(exc)
    return JSONResponse(
        status_code=409,
        content={"detail": detail},
    )


# Registro de routers modulares
app.include_router(health_router)
app.include_router(editoriales_router)
app.include_router(generos_router)
app.include_router(autores_router)
app.include_router(libros_router)
app.include_router(clientes_router)
app.include_router(ventas_router)
