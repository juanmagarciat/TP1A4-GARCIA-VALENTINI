from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError


def parse_integrity_error_detail(exc: IntegrityError) -> str:
    origin = exc.orig
    code = getattr(origin, "sqlstate", None) or getattr(origin, "pgcode", None)
    messages = {
        "23505": "Ya existe un registro con esos datos únicos.",
        "23503": "Uno de los recursos relacionados no existe o está en uso.",
        "23514": "Los datos no cumplen las restricciones del negocio.",
        "23502": "Falta un dato obligatorio.",
    }
    return messages.get(code, "Conflicto de integridad al procesar la operación.")


def get_integrity_http_exception(exc: IntegrityError) -> HTTPException:
    return HTTPException(status_code=409, detail=parse_integrity_error_detail(exc))
