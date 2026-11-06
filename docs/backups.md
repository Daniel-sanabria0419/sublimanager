# Respaldos y recuperación — PostgreSQL

Procedimiento operativo para la base **SubliManager** (PostgreSQL 16). Aplica tanto al contenedor Docker Compose del repo como a una instancia nativa.

## Qué respaldar

| Activo | Ubicación típica | Criticidad |
|--------|------------------|------------|
| Base `sublimanager` | PostgreSQL | Crítica |
| Archivos de diseño | `DESIGNS_ROOT` (p. ej. `./data/disenos`) | Alta |
| `.env` (fuera de git) | Máquina operador | Alta (secretos) |
| Código / migraciones | Repositorio Git | Ya versionado |

Los movimientos de inventario y caja son el histórico contable: un respaldo reciente es la única vía de recuperación ante corrupción o borrado accidental.

## Respaldo lógico (`pg_dump`)

### Con Docker Compose (desarrollo / taller)

```bash
cd /ruta/a/sublimanager

# Dump comprimido con fecha
mkdir -p backups
docker compose exec -T postgres \
  pg_dump -U sublimanager -d sublimanager --format=custom --file=/tmp/sublimanager.dump

docker compose cp postgres:/tmp/sublimanager.dump \
  "./backups/sublimanager-$(date +%Y%m%d-%H%M).dump"
```

Alternativa a stdout (sin copiar archivo del contenedor):

```bash
docker compose exec -T postgres \
  pg_dump -U sublimanager -d sublimanager --format=custom \
  > "./backups/sublimanager-$(date +%Y%m%d-%H%M).dump"
```

### PostgreSQL nativo

```bash
pg_dump -U sublimanager -h localhost -d sublimanager --format=custom \
  -f "./backups/sublimanager-$(date +%Y%m%d-%H%M).dump"
```

### Respaldo de diseños

```bash
tar -czf "./backups/disenos-$(date +%Y%m%d).tar.gz" -C . data/disenos
```

## Frecuencia sugerida

| Contexto | Frecuencia mínima |
|----------|-------------------|
| Taller en producción diaria | Diario (o antes/después de cierre de caja) |
| Desarrollo / pruebas | Antes de experimentos destructivos |
| Antes de `alembic upgrade` en datos reales | Siempre |

Retener al menos 7 copias diarias + 1 semanal fuera de la máquina (USB / nube cifrada).

## Recuperación (`pg_restore`)

1. Detener API y desktop.  
2. Si la BD existe y se va a reemplazar:

```bash
# Ejemplo Docker: recrear BD vacía
docker compose exec -T postgres \
  psql -U sublimanager -d postgres -c "DROP DATABASE IF EXISTS sublimanager;"
docker compose exec -T postgres \
  psql -U sublimanager -d postgres -c "CREATE DATABASE sublimanager OWNER sublimanager;"
```

3. Restaurar:

```bash
# Copiar dump al contenedor si hace falta
docker compose cp ./backups/sublimanager-YYYYMMDD-HHMM.dump postgres:/tmp/restore.dump

docker compose exec -T postgres \
  pg_restore -U sublimanager -d sublimanager --clean --if-exists /tmp/restore.dump
```

Nativo:

```bash
pg_restore -U sublimanager -h localhost -d sublimanager --clean --if-exists \
  ./backups/sublimanager-YYYYMMDD-HHMM.dump
```

4. Verificar migraciones (`alembic current` debe coincidir con el dump).  
5. Restaurar `data/disenos` desde el tar si aplica.  
6. Arrancar API y comprobar `/health/db`.

## Volumen Docker

El Compose usa el volumen nombrado `sublimanager_pgdata`.

```bash
docker compose down          # conserva el volumen
docker compose down -v       # ¡DESTRUYE datos locales!
```

Para respaldar el volumen a nivel de archivo (opcional, mientras el contenedor está parado):

```bash
docker run --rm -v sublimanager_pgdata:/data -v "$PWD/backups:/backup" alpine \
  tar -czf /backup/pgdata-$(date +%Y%m%d).tar.gz -C /data .
```

Preferir `pg_dump` para portabilidad entre hosts.

## Verificación post-restore

```bash
curl -s http://localhost:8000/health/db
# Spot-checks vía API o SQL:
# conteo de pedidos, existencias, últimos movimientos_caja
```

## Lo que no hacer

- No commitear dumps ni `.env` al repositorio.  
- No usar solo copias del directorio de datos mientras Postgres está escrito (riesgo de corrupción) — detener el servicio o usar `pg_dump`.  
- No asumir que `alembic upgrade` recupera datos perdidos: las migraciones crean schema, no reponen filas.
