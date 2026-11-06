# Guía de instalación — SubliManager V1

Instalación desde cero para desarrollo u operación local. Para el día a día tras instalar, ver [`ejecucion.md`](ejecucion.md).

## Requisitos

| Componente | Requisito |
|------------|-----------|
| Python | **3.12+** (`python3.12`) |
| PostgreSQL | **16+** (recomendado vía Docker Compose) |
| Git | Para clonar el repositorio |
| Docker Compose | Opcional pero recomendado |
| Tk (desktop) | En Debian/Ubuntu: `sudo apt install python3-tk` |

## 1. Clonar y entorno virtual

```bash
git clone https://github.com/Daniel-sanabria0419/sublimanager.git
cd sublimanager
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
pip install -r desktop/requirements.txt
```

## 2. Variables de entorno

```bash
cp .env.example .env
```

Variables relevantes (valores por defecto del ejemplo):

| Variable | Uso | Ejemplo |
|----------|-----|---------|
| `DATABASE_URL` | SQLAlchemy + Psycopg 3 | `postgresql+psycopg://sublimanager:sublimanager@localhost:5432/sublimanager` |
| `API_HOST` / `API_PORT` | Bind de Uvicorn | `0.0.0.0` / `8000` |
| `DESIGNS_ROOT` | Carpeta de archivos de diseño (rutas, no binarios en BD) | `./data/disenos` |
| `SUBLIMANAGER_API_URL` | URL base que usa el desktop | `http://127.0.0.1:8000` |
| `TEST_DATABASE_URL` | Solo tests de integración (opcional) | misma URL con BD `_test` |

No commitear `.env` con secretos reales.

## 3. PostgreSQL

### Opción A — Docker Compose (recomendada)

```bash
docker compose up -d
docker compose ps   # healthcheck pg_isready
```

Credenciales alineadas con `.env.example`:

| Campo | Valor |
|-------|-------|
| Usuario | `sublimanager` |
| Contraseña | `sublimanager` |
| Base | `sublimanager` |
| Puerto | `5432` |
| Volumen | `sublimanager_pgdata` |

### Opción B — PostgreSQL nativo

Cree un rol y una base equivalentes y ajuste `DATABASE_URL`. Ejemplo:

```sql
CREATE USER sublimanager WITH PASSWORD 'sublimanager';
CREATE DATABASE sublimanager OWNER sublimanager;
```

SQLite **no** está permitido como BD principal.

## 4. Migraciones Alembic

Con el venv activo y PostgreSQL accesible:

```bash
./scripts/run_migrations.sh
```

Equivale a `alembic upgrade head` desde `backend/` con `PYTHONPATH` correcto.

| Revisión | Contenido |
|----------|-----------|
| `20261106_0001` | Stub vacío (Stage 1) |
| `20261106_0002` | **36 tablas** de negocio + CHECKs, FKs e índices |

Detalle del schema: [`diccionario-datos.md`](diccionario-datos.md).

## 5. Arrancar la API

```bash
./scripts/run_api.sh
```

Comprobar:

```bash
curl -s http://localhost:8000/health
curl -s http://localhost:8000/health/db
```

- OpenAPI interactivo: http://localhost:8000/docs  
- ReDoc: http://localhost:8000/redoc  

## 6. Cliente desktop

En **otra terminal** (mismo venv):

```bash
export SUBLIMANAGER_API_URL=http://127.0.0.1:8000   # opcional si ya está en .env
python -m desktop.main
```

El cliente solo habla REST (HTTPX). Ver [`../desktop/README.md`](../desktop/README.md).

## 7. Carpeta de diseños

```bash
mkdir -p data/disenos
```

Los diseños de pedido guardan `ruta_archivo` (referencia), no el binario en PostgreSQL.

## 8. Tests (opcional en instalación)

```bash
# Crear BD de prueba si usa Docker:
docker compose exec postgres psql -U sublimanager -c "CREATE DATABASE sublimanager_test;"

TEST_DATABASE_URL=postgresql+psycopg://sublimanager:sublimanager@localhost:5432/sublimanager_test \
  ./scripts/run_tests.sh
```

Sin `TEST_DATABASE_URL`, los tests que requieren BD se omiten.

## Checklist post-instalación

1. `docker compose ps` → Postgres healthy  
2. `./scripts/run_migrations.sh` → sin error  
3. `GET /health` y `GET /health/db` → 200  
4. `python -m desktop.main` → shell ERP con indicador de API  
5. Abrir http://localhost:8000/docs y listar un catálogo (p. ej. bodegas)

## Documentación relacionada

- [`ejecucion.md`](ejecucion.md) — operación diaria  
- [`backups.md`](backups.md) — respaldo / recuperación  
- [`api.md`](api.md) — referencia REST  
- [`manual-usuario.md`](manual-usuario.md) — flujos de negocio  
