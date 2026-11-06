# Ejecución diaria — SubliManager V1

Cómo arrancar, detener y operar el sistema una vez instalado ([`instalacion.md`](instalacion.md)).

## Resumen de procesos

| Proceso | Cómo | Puerto / recurso |
|---------|------|------------------|
| PostgreSQL | `docker compose up -d` | `localhost:5432` |
| API FastAPI | `./scripts/run_api.sh` | `http://localhost:8000` |
| Desktop | `python -m desktop.main` | UI local (CustomTkinter) |

Orden recomendado: **Postgres → migraciones (si hubo cambio de schema) → API → desktop**.

## Arranque típico

```bash
cd /ruta/a/sublimanager
source .venv/bin/activate

# 1. Base de datos
docker compose up -d

# 2. API (terminal 1)
./scripts/run_api.sh

# 3. Desktop (terminal 2)
export SUBLIMANAGER_API_URL=http://127.0.0.1:8000
python -m desktop.main
```

Comprobaciones rápidas:

```bash
curl -s http://localhost:8000/health
curl -s http://localhost:8000/health/db
```

En el desktop, la barra superior muestra `API · http://…`. Si la API no responde, aparece aviso tras el arranque.

## Parada

1. Cerrar la ventana del desktop (o Ctrl+C en su terminal).  
2. Detener Uvicorn con Ctrl+C en la terminal de `./scripts/run_api.sh`.  
3. Opcional — detener Postgres:

```bash
docker compose stop          # conserva el volumen de datos
# o
docker compose down          # detiene contenedores; el volumen `sublimanager_pgdata` permanece
```

`docker compose down -v` **borra** el volumen de datos. No usarlo salvo que se quiera destruir la BD local.

## Variables útiles en runtime

| Variable | Efecto |
|----------|--------|
| `SUBLIMANAGER_API_URL` | URL base del cliente desktop |
| `API_HOST` / `API_PORT` | Bind de Uvicorn (leídas por el script / settings) |
| `DATABASE_URL` | Conexión SQLAlchemy |
| `LOG_LEVEL` | Nivel de log del backend (`INFO` por defecto) |
| `DESIGNS_ROOT` | Raíz de archivos de diseño |

## Migraciones después de un `git pull`

Si `main` trae nuevas revisiones Alembic:

```bash
source .venv/bin/activate
./scripts/run_migrations.sh
```

V1 congelado usa `20261106_0001` + `20261106_0002` (36 tablas). No hay downgrade de negocio documentado para producción.

## Logs y diagnóstico

| Síntoma | Qué revisar |
|---------|-------------|
| Desktop no carga datos | API caída; `SUBLIMANAGER_API_URL`; CORS no aplica (mismo host HTTP) |
| `/health/db` falla | Contenedor Postgres; `DATABASE_URL`; puerto 5432 ocupado |
| Error de migración | Postgres vacío vs. parcial; revisar `alembic current` en `backend/` |
| Stock / saldos incorrectos | Operar solo vía API/Services; no editar tablas a mano |

OpenAPI en vivo: http://localhost:8000/docs — útil para probar un endpoint sin el desktop.

## Tests de humo

```bash
./scripts/run_tests.sh
```

Con integración + escenario vaso sublimable:

```bash
TEST_DATABASE_URL=postgresql+psycopg://sublimanager:sublimanager@localhost:5432/sublimanager_test \
  ./scripts/run_tests.sh
```

## Respaldos

Antes de pruebas destructivas o despliegues, ver [`backups.md`](backups.md).

## Flujo de negocio sugerido (operador)

1. Catálogos: bodegas, unidades, categorías, métodos de pago, cuentas de caja.  
2. Materiales / productos / recetas.  
3. Compra → recibir (entra stock + promedio).  
4. Cliente → pedido → (diseño) → producción FABRICADO → pagos → ENTREGADO.  
5. Reportes / dashboard.

Detalle paso a paso: [`manual-usuario.md`](manual-usuario.md).
