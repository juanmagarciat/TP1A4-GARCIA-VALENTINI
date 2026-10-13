# Verificación de entrega — García y Valentini

Fecha: 13 de octubre de 2026. Entorno: Python 3.12, PostgreSQL 16.15, Windows.

- Dependencias instaladas desde cero con `requirements.txt` en un entorno virtual separado.
- `alembic upgrade head` ejecutado sobre una base vacía: correcto.
- `alembic downgrade -1` seguido de `alembic upgrade head`: correcto.
- `alembic check`: sin diferencias entre modelos y esquema.
- `python -m scripts.seed`: carga inicial correcta.
- `python -m unittest discover -s test -v`, con `TP_TEST_RESET=1`: 5 pruebas de integración aprobadas, con múltiples peticiones y aserciones por prueba.
- Archivo `casos_prueba.http`: 47 peticiones ejecutadas en orden, todas con el código esperado.
- C-07: dos SELECT para cada detalle de libro con uno/dos autores y de venta con uno/dos renglones. Consultas ejecutadas en `evidencia_C07.txt`.
- Concurrencia: dos intentos de vender el último ejemplar producen un 201 y un 409, con stock final cero.
- Precio histórico: modificar el precio del libro no altera el precio ni el total de ventas anteriores.
- Transacciones: una venta fallida no descuenta stock; una venta exitosa queda confirmada antes del aviso.
- Asincronía: `/health/live` responde mientras se está ejecutando el aviso de 0,5 segundos.
- Error de disponibilidad simulado: la API responde 503 con mensaje propio, sin devolver la excepción interna.
- Revisión de formato e imports con Ruff: sin errores en las reglas F e I.

Registros: `verificacion.txt`, `verificacion_http.txt`, `verificacion_migraciones.txt` y `verificacion_seed.txt`. La advertencia de deprecación de httpx/TestClient pertenece a una dependencia y no implica una prueba fallida.

Las bases utilizadas para esta verificación fueron aisladas; los datos se reconstruyen con el seed. El código no contiene credenciales reales ni necesita los entornos usados para corregirlo.

En los registros se sustituyeron las rutas absolutas locales por marcadores; los resultados no se modificaron.
