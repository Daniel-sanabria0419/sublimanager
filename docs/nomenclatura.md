# Nomenclatura en español — SubliManager V1

Convención **congelada** para schema PostgreSQL, API, UI y docs de negocio. El stack tecnológico permanece en inglés (FastAPI, SQLAlchemy, Alembic, CustomTkinter, PostgreSQL, Pytest, HTTPX). Tipos SQL (`BIGINT`, `NUMERIC`, `TIMESTAMPTZ`, …) se mantienen.

## Reglas generales

| Elemento | Forma |
|----------|--------|
| Identificadores SQL | `snake_case` español, **sin acentos ni ñ** |
| Tablas | Plural (`pedidos`, `materiales`, `bodegas`) |
| Columnas | Singular descriptivo (`nombre`, `fecha_pedido`, `monto`) |
| FK | Sufijo `_id` (`pedido_id`, `bodega_id`, `cliente_id`) |
| PK | Siempre `id BIGINT` |
| Booleanos | `activo`, `control_stock`, `es_desperdicio` |
| Timestamps | Sufijo `_en` (`creado_en`, `actualizado_en`, `cambiado_en`) |
| Enums / estados | `UPPER_SNAKE` español (`PENDIENTE`, `EN_PRODUCCION`) |
| Paths API | `/api/v1/` + plural **kebab-case** español |
| JSON | Mismos nombres que columnas |

## Paths (ejemplos)

- `/api/v1/pedidos`
- `/api/v1/ordenes-produccion`
- `/api/v1/movimientos-inventario`
- `/api/v1/cuentas-caja`
- `/api/v1/pagos-proveedor`
- `/api/v1/reportes/dashboard`

Lista completa: [`api.md`](api.md).

## Tablas V1 (36)

| Módulo | Tablas |
|--------|--------|
| A Inventario | `categorias_material`, `unidades_medida`, `materiales`, `bodegas`, `existencias`, `movimientos_inventario`, `items_movimiento_inventario` |
| B Productos | `categorias_producto`, `productos`, `variantes_producto`, `tecnicas_produccion`, `tecnicas_producto` |
| C Recetas/Costos | `recetas_producto`, `items_receta_producto`, `perfiles_costo_producto`, `categorias_costo` |
| D Clientes/Pedidos | `clientes`, `pedidos`, `items_pedido`, `disenos_pedido`, `historial_estado_pedido` |
| E Producción | `ordenes_produccion`, `items_orden_produccion`, `consumos_produccion`, `asientos_costo_produccion` |
| F Compras | `proveedores`, `compras`, `items_compra` |
| G Finanzas | `metodos_pago`, `cuentas_caja`, `pagos`, `categorias_gasto`, `gastos`, `pagos_gasto`, `pagos_proveedor`, `movimientos_caja` |

Formas elegidas: `bodegas` (no almacenes), `existencias` (no stocks), `items_*` (no `lineas_*`).

## Decisiones V1

- `ordenes_produccion.pedido_id` es **NOT NULL** (OP sin pedido → fase posterior).  
- En las mismas 36 tablas (no tabla #37): `movimientos_inventario.estado`, `movimientos_inventario.grupo_transferencia_id`.  
- `pedidos.descuento` = monto monetario.  
- Columna `sku` permanece en inglés (código internacional).

## Enums aprobados

| Dominio | Valores |
|---------|---------|
| `pedidos.estado` | `PENDIENTE`, `CONFIRMADO`, `DISENO`, `ESPERANDO_APROBACION`, `EN_PRODUCCION`, `LISTO`, `ENTREGADO`, `CANCELADO` |
| `productos.tipo_producto` | `FABRICADO`, `REVENTA`, `SERVICIO` |
| `movimientos_inventario.tipo_movimiento` | `COMPRA`, `PRODUCCION`, `AJUSTE`, `DESPERDICIO`, `DEVOLUCION`, `TRANSFERENCIA_ENTRADA`, `TRANSFERENCIA_SALIDA`, `VENTA`, `REVERSO` |
| `movimientos_inventario.estado` | `BORRADOR`, `CONFIRMADO`, `ANULADO` |
| `ordenes_produccion.estado` | `PLANIFICADA`, `EN_PROCESO`, `COMPLETADA`, `CANCELADA` |
| `disenos_pedido.estado_aprobacion` | `BORRADOR`, `PENDIENTE_APROBACION`, `APROBADO`, `RECHAZADO` |
| Pagos (`pagos.estado`, …) | `PENDIENTE`, `CONFIRMADO`, `ANULADO` |
| `gastos.estado_pago` | `NO_PAGADO`, `PARCIAL`, `PAGADO`, `ANULADO` |
| `compras.estado` | `BORRADOR`, `RECIBIDA`, `PARCIALMENTE_RECIBIDA`, `CANCELADA` |
| `cuentas_caja.tipo_cuenta` | `EFECTIVO`, `BANCO`, `BILLETERA_DIGITAL`, `OTRO` |
| `movimientos_caja.tipo_movimiento` | `ENTRADA`, `SALIDA` |
| `categorias_costo.tipo_costo` | `MATERIAL`, `MANO_OBRA`, `ELECTRICIDAD`, `DEPRECIACION`, `MANTENIMIENTO`, `EMPAQUE`, `OTRO` |
| `asientos_costo_produccion.etapa_costo` | `ESTIMADO`, `REAL` |

Diccionario detallado: [`diccionario-datos.md`](diccionario-datos.md). Diagrama ER: [`er-diagrama.md`](er-diagrama.md).
