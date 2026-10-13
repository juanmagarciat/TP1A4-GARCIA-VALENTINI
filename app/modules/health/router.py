import logging

from app.core.database import get_session
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/health", tags=["Health"])
logger = logging.getLogger(__name__)


@router.get("/live")
async def liveness():
    return {"estado": "vivo"}


@router.get("/ready")
async def readiness(session: AsyncSession = Depends(get_session, scope="function")):
    try:
        await session.execute(text("SELECT 1"))
        return {"estado": "listo"}
    except Exception:
        logger.exception("Falló la comprobación de disponibilidad de la base")
        raise HTTPException(503, "Base de datos no disponible.") from None
