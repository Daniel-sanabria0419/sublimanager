# Referencia API — SubliManager V1

Prefijo de negocio: **`/api/v1`**.  
Contrato interactivo (fuente de verdad de esquemas request/response):

- Swagger UI: http://localhost:8000/docs  
- ReDoc: http://localhost:8000/redoc  
- OpenAPI JSON: http://localhost:8000/openapi.json  

JSON en `snake_case` español (igual que columnas). Dinero y cantidades como decimales en string/number según Pydantic (preferir precisión decimal).

## Salud

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Proceso vivo (`estado: ok`) |
| GET | `/health/db` | Ping a PostgreSQL |

## Inventario y compras

| Método | Ruta | Notas |
|--------|------|-------|
| CRUD | `/api/v1/categorias-material` | |
| CRUD | `/api/v1/unidades-medida` | |
| CRUD | `/api/v1/bodegas` | |
| POST/GET/PATCH | `/api/v1/materiales` | Alta puede incluir stock vía AJUSTE |
| GET | `/api/v1/materiales/alertas-stock-bajo` | Stock &lt; mínimo |
| GET | `/api/v1/existencias` | Filtros por bodega / material / variante |
| POST/GET | `/api/v1/movimientos-inventario` | Entrada/salida/ajuste |
| POST | `/api/v1/movimientos-inventario/transferencias` | Par SALIDA/ENTRADA + `grupo_transferencia_id` |
| POST | `/api/v1/movimientos-inventario/{id}/confirmar` | `BORRADOR` → `CONFIRMADO` |
| CRUD | `/api/v1/proveedores` | |
| POST/GET | `/api/v1/compras` | Alta en `BORRADOR` |
| POST | `/api/v1/compras/{id}/recibir` | Stock + promedio ponderado |
| POST | `/api/v1/compras/{id}/cancelar` | Solo `BORRADOR` |

## Productos, recetas y costos

| Método | Ruta | Notas |
|--------|------|-------|
| CRUD | `/api/v1/categorias-producto` | |
| POST/GET/PATCH | `/api/v1/productos` | `FABRICADO\|REVENTA\|SERVICIO` |
| GET | `/api/v1/productos/{id}/costo-estimado` | §5.4 |
| POST/GET/PATCH | `/api/v1/variantes-producto` | SKU único |
| CRUD | `/api/v1/tecnicas-produccion` | |
| POST/GET/DELETE | `/api/v1/tecnicas-producto` | Vínculo producto–técnica |
| CRUD | `/api/v1/categorias-costo` | |
| POST/GET | `/api/v1/recetas-producto` | Versionadas + ítems |
| POST | `/api/v1/recetas-producto/{id}/activar` | Desactiva hermanas del alcance |
| POST/GET | `/api/v1/perfiles-costo-producto` | Históricos |
| POST | `/api/v1/perfiles-costo-producto/{id}/activar` | |

## Clientes y pedidos

| Método | Ruta | Notas |
|--------|------|-------|
| CRUD | `/api/v1/clientes` | DELETE = baja lógica |
| POST/GET/PATCH | `/api/v1/pedidos` | Ítems + descuento monto |
| POST | `/api/v1/pedidos/{id}/estado` | Transición validada + historial |
| POST | `/api/v1/pedidos/{id}/cancelar` | → `CANCELADO` |
| GET | `/api/v1/pedidos/{id}/historial-estados` | |
| GET | `/api/v1/pedidos/{id}/saldo` | `total − pagos CONFIRMADOS` |
| POST/GET | `/api/v1/pedidos/{id}/disenos` | `ruta_archivo` |
| PATCH | `/api/v1/pedidos/disenos/{id}` | Aprobación de diseño |
| CRUD | `/api/v1/metodos-pago` | DELETE = baja lógica |
| CRUD | `/api/v1/cuentas-caja` | Incluye `/saldos` y `/{id}/saldo` |
| POST/GET | `/api/v1/pagos` | Anticipos / cobros |
| POST | `/api/v1/pagos/{id}/confirmar` | + `movimientos_caja` (idempotente) |
| POST | `/api/v1/pagos/{id}/anular` | Revierte caja si estaba confirmado |

## Órdenes de producción

| Método | Ruta | Notas |
|--------|------|-------|
| POST/GET | `/api/v1/ordenes-produccion` | `pedido_id` obligatorio |
| GET | `/api/v1/ordenes-produccion/{id}` | Detalle + consumos/asientos |
| GET | `/api/v1/ordenes-produccion/{id}/materiales-requeridos` | Query `bodega_id` |
| POST | `/api/v1/ordenes-produccion/{id}/iniciar` | → `EN_PROCESO` |
| POST | `/api/v1/ordenes-produccion/{id}/cancelar` | Sin consumos |
| POST | `/api/v1/ordenes-produccion/{id}/completar` | Cierre + REAL |
| POST | `/api/v1/ordenes-produccion/{id}/items/{item_id}/consumos` | Descuenta stock 1× |
| POST | `/api/v1/ordenes-produccion/{id}/items/{item_id}/asientos-costo` | Costos REAL no material |
| POST | `/api/v1/ordenes-produccion/{id}/items/{item_id}/cantidades` | Producida/rechazada |
| GET | `/api/v1/ordenes-produccion/{id}/comparacion-costos` | ESTIMADO vs REAL |

## Finanzas (gastos, proveedores, caja, resumen)

| Método | Ruta | Notas |
|--------|------|-------|
| CRUD | `/api/v1/categorias-gasto` | |
| POST/GET/PATCH | `/api/v1/gastos` | `estado_pago` |
| POST | `/api/v1/gastos/{id}/anular` | Sin pagos CONFIRMADOS |
| POST/GET | `/api/v1/pagos-gasto` | → caja `SALIDA` |
| POST | `/api/v1/pagos-gasto/{id}/confirmar` | Idempotente |
| POST | `/api/v1/pagos-gasto/{id}/anular` | |
| POST/GET | `/api/v1/pagos-proveedor` | → caja `SALIDA` |
| GET | `/api/v1/pagos-proveedor/saldo/{compra_id}` | |
| POST | `/api/v1/pagos-proveedor/{id}/confirmar\|anular` | |
| GET | `/api/v1/movimientos-caja` | Solo lectura vía API |
| GET | `/api/v1/finanzas/cuentas-por-cobrar` | Pedidos con saldo &gt; 0 |
| GET | `/api/v1/finanzas/cuentas-por-pagar` | Compras con saldo &gt; 0 |
| GET | `/api/v1/finanzas/resumen` | Ventas / cobrado / CxC / utilidad |

## Reportes

| Método | Ruta |
|--------|------|
| GET | `/api/v1/reportes/ventas/diarias` |
| GET | `/api/v1/reportes/ventas/mensuales` |
| GET | `/api/v1/reportes/productos-mas-vendidos` |
| GET | `/api/v1/reportes/utilidad-por-producto` |
| GET | `/api/v1/reportes/rentabilidad-pedidos` |
| GET | `/api/v1/reportes/costos-produccion` |
| GET | `/api/v1/reportes/costos-por-categoria` |
| GET | `/api/v1/reportes/compras` |
| GET | `/api/v1/reportes/gastos` |
| GET | `/api/v1/reportes/inventario-valorizado` |
| GET | `/api/v1/reportes/consumo-materiales` |
| GET | `/api/v1/reportes/desperdicios` |
| GET | `/api/v1/reportes/cuentas-pendientes` |
| GET | `/api/v1/reportes/dashboard` |
| GET | `/api/v1/reportes/export/{tipo}` | `ventas`, `inventario-valorizado`, `rentabilidad-pedidos`, `resumen-financiero` (+ `formato=csv\|pdf`) |

## Errores

Los Services lanzan excepciones de dominio que la API mapea a HTTP 4xx con mensaje en español. Operaciones multi-tabla son atómicas (rollback completo ante fallo).

## Autenticación

V1 **no** incluye auth multi-usuario. Desplegar solo en red de confianza / localhost.
