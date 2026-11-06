# Nomenclatura en español — referencia Stage 1

Espejo condensado de `nomenclatura-es.md` y `database.md` del Project store
(Stage 0 **aprobado**). Stage 2 materializa las 36 tablas vía Alembic
(`20261106_0002`); esta guía fija el idioma de schema, API y UI.

## Reglas

| Elemento | Forma |
|----------|--------|
| Tablas / columnas SQL | `snake_case` español, **sin acentos ni ñ** |
| Tablas | Plural (`pedidos`, `materiales`, `bodegas`) |
| FK | Sufijo `_id` (`pedido_id`, `bodega_id`) |
| Timestamps | Sufijo `_en` (`creado_en`, `actualizado_en`) |
| Enums / estados | `UPPER_SNAKE` español (`PENDIENTE`, `EN_PRODUCCION`) |
| Paths API | `/api/v1/` + plural kebab-case español |
| Stack tecnológico | Inglés (FastAPI, SQLAlchemy, PostgreSQL, …) |

## Ejemplos de paths (Stage 2+)

- `/api/v1/pedidos`
- `/api/v1/ordenes-produccion`
- `/api/v1/movimientos-inventario`
- `/api/v1/cuentas-caja`

## Tablas V1 (36) — nombres congelados

| Módulo | Tablas |
|--------|--------|
| A Inventario | `categorias_material`, `unidades_medida`, `materiales`, `bodegas`, `existencias`, `movimientos_inventario`, `items_movimiento_inventario` |
| B Productos | `categorias_producto`, `productos`, `variantes_producto`, `tecnicas_produccion`, `tecnicas_producto` |
| C Recetas/Costos | `recetas_producto`, `items_receta_producto`, `perfiles_costo_producto`, `categorias_costo` |
| D Clientes/Pedidos | `clientes`, `pedidos`, `items_pedido`, `disenos_pedido`, `historial_estado_pedido` |
| E Producción | `ordenes_produccion`, `items_orden_produccion`, `consumos_produccion`, `asientos_costo_produccion` |
| F Compras | `proveedores`, `compras`, `items_compra` |
| G Finanzas | `metodos_pago`, `cuentas_caja`, `pagos`, `categorias_gasto`, `gastos`, `pagos_gasto`, `pagos_proveedor`, `movimientos_caja` |

## Decisiones V1 relevantes

- `ordenes_produccion.pedido_id` es **NOT NULL** (OP sin pedido → fase posterior).
- Adiciones en las mismas 36 tablas (no tabla #37):  
  `movimientos_inventario.estado`, `movimientos_inventario.grupo_transferencia_id`.
- Formas elegidas: `bodegas` (no almacenes), `existencias` (no stocks).

## Enums (muestra)

| Dominio | Valores |
|---------|---------|
| `pedidos.estado` | `PENDIENTE`, `CONFIRMADO`, `DISENO`, `ESPERANDO_APROBACION`, `EN_PRODUCCION`, `LISTO`, `ENTREGADO`, `CANCELADO` |
| `productos.tipo_producto` | `FABRICADO`, `REVENTA`, `SERVICIO` |
| `ordenes_produccion.estado` | `PLANIFICADA`, `EN_PROCESO`, `COMPLETADA`, `CANCELADA` |
| `movimientos_inventario.estado` | `BORRADOR`, `CONFIRMADO`, `ANULADO` |
| Pagos (`pagos.estado`, …) | `PENDIENTE`, `CONFIRMADO`, `ANULADO` |
