"""Pruebas reales de PostgreSQL. Usar exclusivamente una base de prueba vacía/preparada."""

import asyncio
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

from app.main import app
from fastapi.testclient import TestClient
from scripts.seed import seed
from sqlalchemy import event


@unittest.skipUnless(
    os.environ.get("TP_TEST_RESET") == "1",
    "Definir TP_TEST_RESET=1 en una base de prueba; se borran sus datos",
)
class Integracion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ids = asyncio.run(seed(reset=True))
        cls.ctx = TestClient(app)
        cls.client = cls.ctx.__enter__()
        cls.evidence = []

    @classmethod
    def tearDownClass(cls):
        cls.ctx.__exit__(None, None, None)
        Path("test/evidencia_C07.txt").write_text(
            "\n".join(cls.evidence), encoding="utf-8"
        )

    def request(self, method, path, expected=200, **kwargs):
        r = self.client.request(method, path, **kwargs)
        self.assertEqual(r.status_code, expected, (path, r.text))
        return r.json() if r.content else None

    def test_01_contratos_y_relaciones(self):
        self.assertEqual(self.request("GET", "/health/live"), {"estado": "vivo"})
        self.request("GET", "/health/ready")
        self.request("GET", "/clientes/abc", 422)
        for path in [
            "/libros/",
            "/ventas/",
            "/editoriales/",
            "/generos/",
            "/autores/",
            "/clientes/",
            "/editoriales/1/libros",
            "/generos/1/libros",
            "/autores/1/libros",
            "/clientes/1/ventas",
        ]:
            self.request("GET", path + "?limit=0", 422)
            self.request("GET", path + "?offset=-1", 422)
            self.request("GET", path + "?limit=101", 422)
        for path in [
            "/editoriales/99999/libros",
            "/generos/99999/libros",
            "/autores/99999/libros",
            "/clientes/99999/ventas",
        ]:
            self.request("GET", path, 404)
        for path in ["/editoriales/1/libros", "/generos/1/libros", "/autores/1/libros"]:
            self.assertEqual(len(self.request("GET", path)), 2)
        self.assertEqual(
            self.request("GET", "/libros/", params={"titulo": "' OR '1'='1"}), []
        )
        self.assertEqual(
            len(self.request("GET", "/libros/", params={"titulo": "RAYU"})), 1
        )
        self.assertEqual(self.request("GET", "/libros/?genero_id=99999"), [])
        for resource, body in [
            ("editoriales", {"pais": "Uruguay"}),
            ("autores", {"nacionalidad": "Uruguaya"}),
            ("clientes", {"nombre": "Actualizado"}),
            ("libros", {"titulo": "Rayuela revisada"}),
        ]:
            updated = self.request("PATCH", f"/{resource}/1", json=body)
            for k, v in body.items():
                self.assertEqual(updated[k], v)
            self.request("PATCH", f"/{resource}/1", 422, json={next(iter(body)): None})
        self.request("PATCH", "/libros/1", json={"genero_id": None})
        self.request("PATCH", "/libros/1", json={"genero_id": 1})
        self.request("PATCH", "/libros/1", 422, json={"genero_id": 0})
        self.request("PATCH", "/libros/1", 422, json={"precio": "100000000.00"})
        self.request(
            "POST",
            "/clientes/",
            409,
            json={"nombre": "Duplicado", "email": "cliente@example.com"},
        )
        profile = {"telefono": "123456", "direccion": "Calle 1"}
        self.request("POST", "/clientes/1/perfil", 201, json=profile)
        self.request("POST", "/clientes/1/perfil", 409, json=profile)
        self.request("POST", "/clientes/99999/perfil", 404, json=profile)
        book = {
            "isbn": "nuevo",
            "titulo": "Prueba",
            "precio": "10.00",
            "stock": 2,
            "editorial_id": 1,
            "genero_id": 1,
            "autores": [{"autor_id": 1, "rol": "autor", "orden": 1}],
        }
        created = self.request("POST", "/libros/", 201, json=book)
        self.assertEqual(len(created["autorias"]), 1)
        self.request("POST", "/libros/", 409, json=book)
        for field in ["editorial_id", "genero_id"]:
            self.request(
                "POST", "/libros/", 409, json={**book, "isbn": field, field: 99999}
            )
        self.request(
            "POST",
            "/libros/",
            409,
            json={
                **book,
                "isbn": "autor-invalido",
                "autores": [{"autor_id": 99999, "rol": "autor", "orden": 1}],
            },
        )
        self.request("POST", "/libros/", 422, json={**book, "autores": []})
        self.request(
            "POST", "/libros/", 422, json={**book, "autorias": book["autores"]}
        )
        other = self.request(
            "POST", "/editoriales/", 201, json={"nombre": "Otra", "pais": "Argentina"}
        )
        updated = self.request(
            "PATCH", f"/libros/{created['id']}", json={"editorial_id": other["id"]}
        )
        self.assertEqual(updated["editorial"]["id"], other["id"])

    def test_02_ventas_y_consultas(self):
        for body in [
            {"cliente_id": 1, "renglones": []},
            {"cliente_id": 1, "renglones": [{"libro_id": 1, "cantidad": 1}] * 2},
            {"cliente_id": 1, "renglones": [{"libro_id": 1, "cantidad": 0}]},
        ]:
            self.request("POST", "/ventas/", 422, json=body)
        self.request(
            "POST",
            "/ventas/",
            409,
            json={"cliente_id": 99999, "renglones": [{"libro_id": 1, "cantidad": 1}]},
        )
        self.request(
            "POST",
            "/ventas/",
            409,
            json={"cliente_id": 1, "renglones": [{"libro_id": 99999, "cantidad": 1}]},
        )
        self.request(
            "POST",
            "/ventas/",
            422,
            json={
                "cliente_id": 1,
                "total": "1.00",
                "renglones": [{"libro_id": 1, "cantidad": 1}],
            },
        )
        sales = []
        for lines in [
            [{"libro_id": 1, "cantidad": 1}],
            [{"libro_id": 1, "cantidad": 2}, {"libro_id": 2, "cantidad": 1}],
        ]:
            sale = self.request(
                "POST", "/ventas/", 201, json={"cliente_id": 1, "renglones": lines}
            )
            sales.append(sale)
        self.assertEqual(Decimal(sales[1]["total"]), Decimal("71000.00"))
        self.assertEqual(sales[1]["renglones"][0]["titulo"], "Rayuela revisada")
        self.request("PATCH", "/libros/1", json={"precio": "26000.00"})
        detail = self.request("GET", f"/ventas/{sales[1]['id']}")
        self.assertEqual(
            Decimal(detail["renglones"][0]["precio_unitario"]), Decimal("25000.00")
        )
        self.assertEqual(len(self.request("GET", "/clientes/1/ventas")), 2)
        self.request("PATCH", f"/ventas/{sales[0]['id']}", 405, json={"total": "0"})
        for path in ["/libros/1", "/libros/2", *[f"/ventas/{s['id']}" for s in sales]]:
            queries = []

            def capture(conn, cursor, statement, parameters, context, executemany):
                if statement.lstrip().upper().startswith("SELECT"):
                    queries.append(statement)

            engine = app.state.engine.sync_engine
            event.listen(engine, "before_cursor_execute", capture)
            try:
                self.request("GET", path)
            finally:
                event.remove(engine, "before_cursor_execute", capture)
            self.assertEqual(len(queries), 2, (path, queries))
            self.evidence.append(
                f"GET {path}: {len(queries)} SELECT; respuesta 200\n"
                + "\n\n".join(queries)
                + "\n"
            )

    def test_03_stock_concurrente_y_rollback(self):
        book = self.request(
            "POST",
            "/libros/",
            201,
            json={
                "isbn": "concurrencia",
                "titulo": "Último ejemplar",
                "precio": "10.00",
                "stock": 1,
                "editorial_id": 1,
                "autores": [{"autor_id": 1, "rol": "autor", "orden": 1}],
            },
        )
        payload = {
            "cliente_id": 1,
            "renglones": [{"libro_id": book["id"], "cantidad": 1}],
        }
        with ThreadPoolExecutor(max_workers=2) as pool:
            codes = list(
                pool.map(
                    lambda _: self.client.post("/ventas/", json=payload).status_code,
                    range(2),
                )
            )
        self.assertEqual(sorted(codes), [201, 409])
        self.assertEqual(self.request("GET", f"/libros/{book['id']}")["stock"], 0)
        before = self.request("GET", "/libros/1")["stock"]
        self.request(
            "POST",
            "/ventas/",
            409,
            json={
                "cliente_id": 1,
                "renglones": [
                    {"libro_id": 1, "cantidad": 1},
                    {"libro_id": 99999, "cantidad": 1},
                ],
            },
        )
        self.assertEqual(self.request("GET", "/libros/1")["stock"], before)

    def test_04_background_no_bloquea_y_confirma_antes(self):
        import threading
        from unittest.mock import patch

        from app.modules.ventas import service

        started = threading.Event()
        finished = threading.Event()
        original = service.enviar_comprobante

        async def observed(venta_id, email):
            started.set()
            try:
                await original(venta_id, email)
            finally:
                finished.set()

        before = len(self.request("GET", "/ventas/"))
        with patch.object(service, "enviar_comprobante", observed):
            with ThreadPoolExecutor(max_workers=1) as pool:
                pending = pool.submit(
                    self.client.post,
                    "/ventas/",
                    json={
                        "cliente_id": 1,
                        "renglones": [{"libro_id": 2, "cantidad": 1}],
                    },
                )
                self.assertTrue(started.wait(3))
                self.request("GET", "/health/live")
                self.assertFalse(
                    finished.is_set(), "El health debe responder durante el aviso"
                )
                self.assertEqual(len(self.request("GET", "/ventas/")), before + 1)
                self.assertEqual(pending.result(timeout=5).status_code, 201)
        self.assertTrue(finished.is_set())

    def test_05_health_no_expone_error_interno(self):
        from app.core.database import get_session

        class FailedSession:
            async def execute(self, *args, **kwargs):
                raise RuntimeError("DETALLE_INTERNO_NO_PUBLICAR")

        async def failed_session():
            yield FailedSession()

        app.dependency_overrides[get_session] = failed_session
        try:
            with self.assertLogs("app.modules.health.router", level="ERROR"):
                result = self.request("GET", "/health/ready", 503)
            self.assertEqual(result, {"detail": "Base de datos no disponible."})
        finally:
            app.dependency_overrides.pop(get_session, None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
