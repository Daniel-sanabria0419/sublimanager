# SubliManager

ERP de sublimación (**V1 completo**): backend FastAPI + PostgreSQL y cliente desktop CustomTkinter desacoplados por REST.

**Estado:** Stages 1–11 entregados — schema de 36 tablas, inventario, productos, pedidos, producción, finanzas, desktop, reportes, QA y documentación de entrega.

## Stack

- Python 3.12+
- FastAPI · Uvicorn · Pydantic 2 · SQLAlchemy 2.0 · Alembic · Psycopg 3
- PostgreSQL 16+
- Pytest · HTTPX
- Desktop: CustomTkinter + HTTPX + Matplotlib (sin acceso a BD)

## Estructura

```
sublimanager/
├── backend/           # API FastAPI (Services + 36 tablas)
├── desktop/           # Cliente CustomTkinter
├── docs/              # Guías en español (instalación, manual, API, …)
├── scripts/           # Arranque, migraciones y tests
├── docker-compose.yml # PostgreSQL local
├── .env.example
└── README.md
```

## Requisitos

| Componente | Versión |
|------------|---------|
| Python | 3.12+ |
| PostgreSQL | 16+ (Docker Compose incluido) |
| Sistema | Linux / macOS / Windows (Tk disponible) |
| Opcional | Docker / Docker Compose |

En Debian/Ubuntu para el desktop: `sudo apt install python3-tk`.

## Arranque rápido

```bash
git clone https://github.com/Daniel-sanabria0419/sublimanager.git
cd sublimanager
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
pip install -r desktop/requirements.txt
cp .env.example .env
docker compose up -d          # PostgreSQL
./scripts/run_migrations.sh   # Alembic → head (36 tablas)
./scripts/run_api.sh          # http://localhost:8000
python -m desktop.main        # cliente ERP (otra terminal)
```

| Recurso | URL |
|---------|-----|
| Salud | http://localhost:8000/health |
| Salud BD | http://localhost:8000/health/db |
| OpenAPI (Swagger) | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

## Documentación

| Guía | Contenido |
|------|-----------|
| [`docs/instalacion.md`](docs/instalacion.md) | Instalación completa (Postgres, env, migraciones, API, desktop) |
| [`docs/ejecucion.md`](docs/ejecucion.md) | Uso diario: arranque, parada, logs, tests |
| [`docs/manual-usuario.md`](docs/manual-usuario.md) | Flujos de operador (pedidos, inventario, producción, finanzas, reportes) |
| [`docs/api.md`](docs/api.md) | Resumen de endpoints REST + enlace a OpenAPI |
| [`docs/arquitectura.md`](docs/arquitectura.md) | Capas, invariantes y layout |
| [`docs/reglas-negocio.md`](docs/reglas-negocio.md) | Reglas §5.1–5.10 (Services) |
| [`docs/diccionario-datos.md`](docs/diccionario-datos.md) | Diccionario de las 36 tablas |
| [`docs/er-diagrama.md`](docs/er-diagrama.md) | Diagrama ER (Mermaid) |
| [`docs/backups.md`](docs/backups.md) | Respaldo y recuperación PostgreSQL |
| [`docs/nomenclatura.md`](docs/nomenclatura.md) | Convención español schema/API/UI |
| [`desktop/README.md`](desktop/README.md) | Cliente desktop |

## Tests

```bash
./scripts/run_tests.sh
# Con BD de prueba (recomendado — integración + escenario §10):
TEST_DATABASE_URL=postgresql+psycopg://sublimanager:sublimanager@localhost:5432/sublimanager_test \
  ./scripts/run_tests.sh
```

Escenario de aceptación: `backend/tests/test_aceptacion_e2e.py`
(proveedor → compra → vaso personalizado → pedido → OP → pagos → ENTREGADO).

## Convenciones

- Identificadores de producto/schema/UI/API en **español** (`pedidos`, `bodegas`, `ordenes_produccion`, …). Ver [`docs/nomenclatura.md`](docs/nomenclatura.md).
- Nombres de stack tecnológico en inglés.
- Sin secretos en el código; solo `.env.example` en el repo.
- El desktop **nunca** habla con PostgreSQL: solo HTTP JSON hacia la API.

## Licencia / autor

Proyecto privado — Sublisoft / Daniel Sanabria.
