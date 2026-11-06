# Guía de instalación — SubliManager V1 (Stage 1)

## Requisitos

- Python **3.12+**
- PostgreSQL **16+** (recomendado vía Docker Compose)
- Git

## 1. Clonar y entorno virtual

```bash
git clone https://github.com/Daniel-sanabria0419/sublimanager.git
cd sublimanager
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

## 2. Variables de entorno

```bash
cp .env.example .env
# Editar DATABASE_URL si hace falta
```

## 3. PostgreSQL local (Docker Compose)

```bash
docker compose up -d
```

Credenciales por defecto (alineadas con `.env.example`):

| Variable | Valor |
|----------|-------|
| Usuario | `sublimanager` |
| Contraseña | `sublimanager` |
| Base | `sublimanager` |
| Puerto | `5432` |

Sin Docker, cree una base PostgreSQL equivalente y ajuste `DATABASE_URL`.

## 4. Migraciones Alembic

Desde la raíz del repo (con el venv activo y `.env` cargado):

```bash
cd backend
export PYTHONPATH=.
alembic upgrade head
```

O:

```bash
./scripts/run_migrations.sh
```

En Stage 1 la migración inicial es **vacía** (solo historial Alembic). Las 36 tablas llegan en Stage 2.

## 5. Arrancar la API

```bash
cd backend
export PYTHONPATH=.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

O: `./scripts/run_api.sh`

Comprobar:

- `GET http://localhost:8000/health` → `200` (`estado: ok`)
- `GET http://localhost:8000/health/db` → `200` si PostgreSQL responde

Documentación interactiva: `http://localhost:8000/docs`

## 6. Tests

```bash
cd backend
export PYTHONPATH=.
pytest -q
```

Los tests de BD se **omiten** si no existe `TEST_DATABASE_URL`. Para forzarlos:

```bash
export TEST_DATABASE_URL=postgresql+psycopg://sublimanager:sublimanager@localhost:5432/sublimanager
pytest -q
```

## Notas de arquitectura (Stage 1)

- Backend FastAPI desacoplado del desktop CustomTkinter.
- PostgreSQL es la única BD principal (no SQLite).
- Identificadores de producto/schema en **español** (ver nomenclatura del Project store); stack en inglés.
- Sin lógica de inventario, productos ni pedidos en esta etapa.
