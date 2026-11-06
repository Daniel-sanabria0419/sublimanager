#!/usr/bin/env bash
# Aplica migraciones Alembic (requiere DATABASE_URL / .env con PostgreSQL).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/backend"
export PYTHONPATH="${ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
exec alembic upgrade head
