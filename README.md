# TP integrador, capítulos 1 a 4 — García y Valentini

**Materia:** Programación III · Tecnicatura Universitaria en Programación a Distancia  
**Integrantes:** Juan Martín García ([juanmagarciat](https://github.com/juanmagarciat)) y Tiziano Valentini ([TiziIV](https://github.com/TiziIV))  
**Tema:** Librería: catálogo, clientes y ventas con FastAPI y PostgreSQL.

## Puesta en marcha

Requisitos: Python 3.12 y PostgreSQL 16 o superior. Ejecutar los comandos desde esta carpeta.
Crear previamente una base vacía `libreria_db` y un usuario con permisos sobre esa base, mediante pgAdmin o `createdb`. Las credenciales se configuran localmente y no se entregan.

Windows / PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item env.example .env
```

Editar `.env`: reemplazar `USUARIO` y `CONTRASENA` por los valores locales. La URL debe comenzar con `postgresql+asyncpg://`. Si la contraseña contiene caracteres reservados de una URL, deben codificarse. No subir `.env`.

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m scripts.seed
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Linux / macOS: `python3 -m venv .venv`, `source .venv/bin/activate`, `python -m pip install -r requirements.txt`, `cp env.example .env`; luego los mismos comandos con `python`.

Documentación interactiva: http://127.0.0.1:8000/docs. Diagnóstico SQL: definir `SQL_ECHO=true` en `.env` y reiniciar el servidor.

## Datos iniciales y pruebas

El seed crea una editorial, un género, dos autores, un cliente y dos libros (uno con un autor y otro con dos). Los precios son 25000.00 y 21000.00, con stock 20 cada uno. La antología es un dato ficticio de prueba.

Para recuperar exactamente ese estado en una **base de prueba**:

```powershell
.\.venv\Scripts\python.exe -m scripts.seed --reset
```

`--reset` borra todos los datos de las tablas del TP en la base indicada por `DATABASE_URL` y reinicia sus secuencias. No ejecutar contra datos que se quieran conservar.

Después del reset, ejecutar en orden `test/casos_prueba.http` usando REST Client de VS Code. Incluye C-01 a C-08, PATCH, navegación inversa, paginación y validaciones. Las ventas se consultan por el ID devuelto, sin suponer IDs tras inserciones fallidas.

Pruebas automatizadas con PostgreSQL real, sobre una base exclusiva para pruebas ya migrada:

```powershell
$env:TP_TEST_RESET="1"
.\.venv\Scripts\python.exe -m unittest discover -s test -v
Remove-Item Env:TP_TEST_RESET
```

Las pruebas reinician los datos y dejan registros adicionales. Antes de volver a usar el archivo `.http`, ejecutar nuevamente el seed con `--reset`. Las pruebas verifican contratos, integridad, relaciones, precio histórico, rollback y competencia por el último ejemplar. Generan `test/evidencia_C07.txt` con las consultas SQL efectivamente ejecutadas. Para Linux/macOS: `TP_TEST_RESET=1 python -m unittest discover -s test -v`.

## Migraciones

El esquema se crea exclusivamente con Alembic; no hay `create_all`. Se entregan dos revisiones autogeneradas contra PostgreSQL y revisadas:

1. `0001_initial_schema`: todas las tablas salvo `genero`, sin `libro.genero_id`.
2. `0002_add_generos`: agrega `genero`, su índice único y `libro.genero_id` nullable con índice y FK.

Los comentarios en cada archivo indican los ajustes manuales: importación del tipo `AutoString` y nombre explícito de la FK de género para su reversión.

```powershell
.\.venv\Scripts\python.exe -m alembic downgrade -1
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic check
```

El downgrade elimina las clasificaciones por género; usar este ciclo sobre una base de prueba. `alembic check` verifica que los modelos y el esquema no requieren otra migración.

## Modelo y decisiones

- `libro.editorial_id` está en el lado muchos: varios libros comparten una editorial. `genero_id` funciona igual, pero admite NULL.
- `libro_autor` es un objeto de asociación con PK `(libro_id, autor_id)`, `rol` y `orden`; ambos extremos tienen navegación.
- `perfil_cliente.cliente_id` es único: un cliente tiene a lo sumo un perfil, representado por un objeto y no una lista.
- `venta.cliente_id` representa la asociación con un cliente existente.
- `renglon_venta.venta_id` expresa la composición: los renglones se construyen dentro de `venta.renglones`, sin endpoint de alta independiente. `libro_id` referencia un libro existente.
- Las FK tienen índices; la base impone UNIQUE, CHECK y las referencias. El alta de libros inserta los IDs recibidos sin consultas previas de existencia.
- Dinero: `Decimal` y `NUMERIC(10,2)` / `NUMERIC(12,2)`. Los precios históricos se copian desde el libro; total y subtotales se calculan en el servidor.
- Las lecturas usan `joinedload` para relaciones a uno y `selectinload` para colecciones. Los detalles de libro y venta emiten dos SELECT con uno o varios elementos. El orden de autorías y renglones es explícito.
- El motor y la fábrica de sesiones nacen en `lifespan`; el cierre libera el motor incluso ante excepciones. Se usa `expire_on_commit=False`.
- `Depends(get_session, scope="function")` confirma la transacción antes de enviar la respuesta y antes del comprobante. Ante un error, la sesión revierte la operación. La versión de FastAPI está fijada para soportar ese alcance.
- El comprobante se agenda con `BackgroundTasks`, `await asyncio.sleep(0.5)` y log. No se bloquea el bucle de eventos.
- Al vender, los libros se bloquean con `SELECT ... FOR UPDATE` en orden de ID, para evitar vender simultáneamente el mismo stock.
- Los errores de integridad se traducen por SQLSTATE a mensajes propios (409). Los DTO rechazan datos inválidos y campos desconocidos (422). PATCH conserva campos omitidos; solo `genero_id` admite null.

## Contratos HTTP

`POST /libros/` recibe `autores`, por ejemplo:

```json
{"isbn":"978-950-00-0003-3","titulo":"Ejemplo","precio":"21000.00","stock":4,"editorial_id":1,"genero_id":1,"autores":[{"autor_id":1,"rol":"autor","orden":1}]}
```

La respuesta de libro incluye `editorial`, `genero` y `autorias` con los datos de cada autor. `POST /ventas/` recibe únicamente `cliente_id` y `renglones` con `libro_id` y `cantidad`. No acepta fecha, precio ni total del cliente. No hay PATCH de ventas.

Las actualizaciones de editorial, autor, libro y cliente usan PATCH. Se incluyen `/editoriales/{id}/libros`, `/generos/{id}/libros`, `/autores/{id}/libros` (con rol y orden) y `/clientes/{id}/ventas`. Todos los listados aceptan `limit` (1–100; defecto 20) y `offset` (desde 0). El listado de libros permite `titulo` sin distinguir mayúsculas y `genero_id`, mediante parámetros ligados.

## Contenido de la entrega

- `app/`: módulos funcionales, modelos, contratos, servicios, routers y configuración.
- `migrations/`: configuración asincrónica y dos revisiones.
- `scripts/seed.py`: carga inicial reproducible.
- `test/`: casos HTTP, pruebas automatizadas, evidencia SQL y registro de verificación.
- `requirements.txt`, `env.example`, `.gitignore` y este README.

No se incluyen `.env`, entornos virtuales, cachés, repositorios internos ni archivos de herramientas auxiliares.
