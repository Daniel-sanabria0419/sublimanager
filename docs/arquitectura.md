# Arquitectura — resumen (Stage 6)

Documento espejo condensado de la arquitectura V1. Nomenclatura de schema/API:
[`nomenclatura.md`](nomenclatura.md). Schema: [`database.md`](database.md).

## Capas

| Capa | Tecnología | Rol |
|------|------------|-----|
| Desktop | CustomTkinter + HTTPX | UI (Stage 8); stub en Stage 1 |
| API | FastAPI / Uvicorn | Único canal REST (`/api/v1/…` en español) |
| Dominio | Services Python | Reglas de negocio (Stage 3–6: inventario, productos, pedidos, producción) |
| Persistencia | SQLAlchemy 2.0 + Alembic + PostgreSQL (Psycopg 3) | Datos y migraciones |

## Invariantes

1. El desktop **nunca** abre conexiones a PostgreSQL ni importa SQLAlchemy.
2. Secretos solo por variables de entorno (`.env`); el repo solo incluye `.env.example`.
3. Sin SQLite como BD principal.
4. Identificadores de negocio (tablas, columnas, estados, UI, paths) en **español**.
5. `ordenes_produccion.pedido_id` es **NOT NULL** en V1.
6. Inventario solo cambia vía `movimientos_inventario` (+ `existencias`); Decimal ROUND_HALF_UP.
7. Recetas y perfiles de costo son **históricos**: nueva versión/fila; no sobrescribir.
8. Crear/editar pedido **no** descuenta inventario; `descuento` es monto; snapshots de precio/costo en `items_pedido`.
9. Diseños de pedido guardan solo `ruta_archivo` (sin binarios en BD).
10. Consumos de OP descuentan inventario **una sola vez** por consumo confirmado (`tipo_referencia=consumo_produccion`).
11. Estados OP: `PLANIFICADA | EN_PROCESO | COMPLETADA | CANCELADA`; `produced + rejected ≤ planned`.

## Layout del backend (`backend/app/`)

- `core/` — config, database, exceptions, constants, logging
- `models/` — 36 tablas SQLAlchemy 2.0 (paquetes A–G) + enums español
- `schemas/` — DTOs Pydantic (inventario, compras, productos, recetas, pedidos, producción, finanzas mín.)
- `repositories/` — persistencia sin orquestar multi-agregado
- `services/` — autoridad de reglas §5.1–5.7 y §5.8 (anticipos mínimos)
- `api/v1/` — routers REST en español
- `utils/decimal_policy.py` — `money_round` / `qty_round` / promedio ponderado

## Endpoints

### Salud (Stage 1)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Proceso vivo |
| GET | `/health/db` | Ping PostgreSQL |

### Inventario y compras (Stage 3)

| Método | Ruta | Descripción |
|--------|------|-------------|
| CRUD | `/api/v1/categorias-material` | Categorías de material |
| CRUD | `/api/v1/unidades-medida` | Unidades de medida |
| CRUD | `/api/v1/bodegas` | Bodegas |
| CRUD | `/api/v1/materiales` | Materiales (+ stock apertura vía AJUSTE) |
| GET | `/api/v1/materiales/alertas-stock-bajo` | Stock &lt; mínimo |
| GET | `/api/v1/existencias` | Consulta de existencias |
| POST/GET | `/api/v1/movimientos-inventario` | Movimientos (entrada/salida/ajuste) |
| POST | `/api/v1/movimientos-inventario/transferencias` | Par SALIDA/ENTRADA |
| POST | `/api/v1/movimientos-inventario/{id}/confirmar` | Confirma BORRADOR |
| CRUD | `/api/v1/proveedores` | Proveedores |
| POST/GET | `/api/v1/compras` | Compras en BORRADOR |
| POST | `/api/v1/compras/{id}/recibir` | Recepción → stock + promedio |
| POST | `/api/v1/compras/{id}/cancelar` | Solo BORRADOR |

### Productos y recetas (Stage 4)

| Método | Ruta | Descripción |
|--------|------|-------------|
| CRUD | `/api/v1/categorias-producto` | Categorías de producto |
| POST/GET/PATCH | `/api/v1/productos` | Productos `FABRICADO\|REVENTA\|SERVICIO` |
| GET | `/api/v1/productos/{id}/costo-estimado` | Costo unitario estimado (§5.4) |
| POST/GET/PATCH | `/api/v1/variantes-producto` | Variantes (SKU único) |
| CRUD | `/api/v1/tecnicas-produccion` | Técnicas de producción |
| POST/GET/DELETE | `/api/v1/tecnicas-producto` | Vínculo producto–técnica (unique) |
| CRUD | `/api/v1/categorias-costo` | Categorías de costo |
| POST/GET | `/api/v1/recetas-producto` | Recetas versionadas + ítems |
| POST | `/api/v1/recetas-producto/{id}/activar` | Activa versión (desactiva hermanas) |
| POST/GET | `/api/v1/perfiles-costo-producto` | Perfiles históricos (`vigente_desde`) |
| POST | `/api/v1/perfiles-costo-producto/{id}/activar` | Activa perfil del alcance |

### Clientes y pedidos (Stage 5)

| Método | Ruta | Descripción |
|--------|------|-------------|
| CRUD | `/api/v1/clientes` | Clientes (DELETE = baja lógica) |
| POST/GET/PATCH | `/api/v1/pedidos` | Pedidos con ítems, descuento monto, totales |
| POST | `/api/v1/pedidos/{id}/estado` | Transición validada + historial |
| POST | `/api/v1/pedidos/{id}/cancelar` | → `CANCELADO` |
| GET | `/api/v1/pedidos/{id}/historial-estados` | Historial de estados |
| GET | `/api/v1/pedidos/{id}/saldo` | `total − pagos CONFIRMADOS` |
| POST/GET | `/api/v1/pedidos/{id}/disenos` | Diseños (`ruta_archivo`, versiones) |
| PATCH | `/api/v1/pedidos/disenos/{id}` | Estado de aprobación |
| POST/GET | `/api/v1/metodos-pago` | Catálogo mínimo para anticipos |
| POST/GET | `/api/v1/cuentas-caja` | Catálogo mínimo para anticipos |
| POST/GET | `/api/v1/pagos` | Anticipos/pagos de pedido |
| POST | `/api/v1/pagos/{id}/confirmar` | → `CONFIRMADO` + `movimientos_caja` |
| POST | `/api/v1/pagos/{id}/anular` | Anula `PENDIENTE` |

### Órdenes de producción (Stage 6)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST/GET | `/api/v1/ordenes-produccion` | Crear OP desde pedido (ítems FABRICADO) / listar |
| GET | `/api/v1/ordenes-produccion/{id}` | Detalle con consumos y asientos |
| GET | `/api/v1/ordenes-produccion/{id}/materiales-requeridos` | Receta activa + disponibilidad (`bodega_id`) |
| POST | `/api/v1/ordenes-produccion/{id}/iniciar` | `PLANIFICADA` → `EN_PROCESO` |
| POST | `/api/v1/ordenes-produccion/{id}/cancelar` | Cancelar sin consumos (reversos diferidos) |
| POST | `/api/v1/ordenes-produccion/{id}/completar` | Cierre + consolidación MATERIAL REAL + PT opcional |
| POST | `/api/v1/ordenes-produccion/{id}/items/{item_id}/consumos` | Consumo/desperdicio → movimiento único |
| POST | `/api/v1/ordenes-produccion/{id}/items/{item_id}/asientos-costo` | Costos REAL no material |
| POST | `/api/v1/ordenes-produccion/{id}/items/{item_id}/cantidades` | Producida/rechazada (+ entrada PT si aplica) |
| GET | `/api/v1/ordenes-produccion/{id}/comparacion-costos` | ESTIMADO vs REAL |
