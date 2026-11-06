# Reglas de negocio — SubliManager V1

Contrato formal de los **Services** (Stages 3–7 + reportes Stage 9). Identificadores en español ([`nomenclatura.md`](nomenclatura.md)). Schema: [`diccionario-datos.md`](diccionario-datos.md).

Notación: `MUST` / `MUST NOT` / `SHOULD`.

## 0. Premisas

- Toda regla se ejecuta en Services, en **transacciones** cuando hay multi-tabla.  
- Dinero y cantidades: `Decimal` (nunca `float`).  
- Inventario solo cambia vía `movimientos_inventario` + ítems (+ `existencias`).  
- Snapshots de precio/costo no se reescriben al cambiar el catálogo.  
- Redondeo **ROUND_HALF_UP**: dinero 2 decimales; cantidades 4. Helper: `backend/app/utils/decimal_policy.py`.  
- Totales: `line_subtotal = money_round(qty × unit_price)`; `pedidos.total = money_round(subtotal − descuento)` con `descuento` como **monto**.

---

## 5.1 Materiales e inventario

- Alta de material MUST tener `categoria_id` y `unidad_id` activos; `stock_minimo ≥ 0`.  
- Stock de apertura: movimiento `AJUSTE` (MUST NOT alterar `existencias` sin movimiento).  
- `costo_promedio` MUST NOT editarse libremente; solo Services autorizados (recepción de compra / ajustes explícitos).  
- `existencias`: XOR `material_id` | `variante_producto_id`; `cantidad ≥ 0`.  
- Tipos de movimiento: `COMPRA | PRODUCCION | AJUSTE | DESPERDICIO | DEVOLUCION | TRANSFERENCIA_ENTRADA | TRANSFERENCIA_SALIDA | VENTA | REVERSO`.  
- Estado: `BORRADOR | CONFIRMADO | ANULADO`. Confirmados MUST NOT eliminarse.  
- Transferencias: mismo `grupo_transferencia_id` en el par SALIDA/ENTRADA.  
- Cantidad de línea siempre `> 0`; la dirección la define el **tipo**.

## 5.2 Compras

| Estado | Inventario | Promedio |
|--------|------------|----------|
| `BORRADOR` | MUST NOT tocar stock | — |
| `RECIBIDA` / `PARCIALMENTE_RECIBIDA` | Entrada `COMPRA` | Actualiza `costo_promedio` |
| `CANCELADA` | Sin movimientos nuevos; si ya hubo recepción → solo vía `REVERSO` | — |

Promedio ponderado materiales:

\[
costo\_promedio_{nuevo} = \frac{(q_{stock}\times c_{viejo}) + (q_{rec}\times c_{unit})}{q_{stock}+q_{rec}}
\]

Si stock previo = 0 → `costo_promedio = costo_unitario` de la recepción. Recepción MUST ser atómica.

## 5.3 Pedidos

- Crear/editar pedido MUST NOT descontar materiales ni terminados.  
- `SERVICIO`: sin consumo automático ni OP por defecto.  
- `REVENTA`: sin OP; salida `VENTA` al pasar a **`ENTREGADO`** (si `control_stock`), atómico.  
- `FABRICADO`: elegible a OP; materiales en producción (§5.5).  
- Snapshots en `items_pedido`; `descuento` = monto.  
- Estados: `PENDIENTE | CONFIRMADO | DISENO | ESPERANDO_APROBACION | EN_PRODUCCION | LISTO | ENTREGADO | CANCELADO`.  
- Toda transición MUST registrar `historial_estado_pedido`.  
- Diseños: `BORRADOR | PENDIENTE_APROBACION | APROBADO | RECHAZADO`.

## 5.4 Costo estimado

- **FABRICADO:** materiales (con % desperdicio estimado) + perfil de costo activo.  
- **REVENTA:** costo de adquisición; MUST NOT sumar receta de fabricación.  
- **SERVICIO:** mano de obra + otros (sin materiales de receta).  
- Utilidad / margen sobre precio de venta; UI solo vía API.

## 5.5 Producción

1. Toda OP MUST tener `pedido_id` NOT NULL (V1).  
2. Ítems de OP referencian `items_pedido`.  
3. Antes de consumir: receta activa + disponibilidad en bodega.  
4. `consumos_produccion` con `costo_unitario_snapshot`.  
5. Descontar inventario **una sola vez** por consumo confirmado.  
6. `cantidad_producida + cantidad_rechazada ≤ cantidad_planificada`.  
7. Desperdicio real: `es_desperdicio = true` (o movimiento `DESPERDICIO`).  
8. Estados OP: `PLANIFICADA | EN_PROCESO | COMPLETADA | CANCELADA`.

## 5.6 Desperdicios

| Clase | Origen | Uso |
|-------|--------|-----|
| Estimado | `%` en ítems de receta | Solo costo estimado |
| Real | Consumos / movimientos | Costo real y consumo total |

MUST NOT inventar desperdicio real = estimado al cerrar.

## 5.7 Costo real

Al cerrar la OP: consolidar `asientos_costo_produccion` con `etapa_costo = REAL`. Comparar ESTIMADO vs REAL. `gasto_id` opcional sin doble conteo en reportes (§5.9).

## 5.8 Pagos de pedidos

- Anticipos, parciales y pago completo permitidos.  
- \(P\) = suma de pagos `CONFIRMADO`; `saldo = total − P`.  
- Nuevo pago: `monto > 0` y `monto ≤ saldo` (bloqueo de fila / `SELECT FOR UPDATE` bajo concurrencia).  
- Estados: `PENDIENTE | CONFIRMADO | ANULADO`.  
- Al confirmar: exactamente un `movimientos_caja` `ENTRADA` (`pago_id`).  
- Anticipos MUST NOT contarse como ventas adicionales (§5.10).

## 5.9 Gastos y proveedores

- Compra de inventario ≠ gasto operativo.  
- `pagos_proveedor` / `pagos_gasto` → caja `SALIDA`.  
- `gastos.estado_pago`: `NO_PAGADO | PARCIAL | PAGADO | ANULADO`.  
- Si un gasto ya alimenta asientos de OP vía `gasto_id`, reportes MUST NOT sumarlo dos veces sin clasificación.

## 5.10 Finanzas — diferenciación

| Concepto | Significado |
|----------|-------------|
| Ventas | Pedidos **`ENTREGADO`** (reconocimiento Stage 9) |
| Caja | `movimientos_caja` / saldos de cuentas |
| Costos | Fabricación estimada/real |
| Gastos | `gastos` operativos |
| Utilidad | Ventas reconocidas − costos − gastos (definición de reportes) |

`movimientos_caja` MUST tener exactamente una FK de origen (`pago_id` XOR `pago_proveedor_id` XOR `pago_gasto_id`). Generados por Services; MUST NOT duplicarse.

---

## Matriz Service → reglas

| Service | Reglas |
|---------|--------|
| Inventario / materiales | 5.1 |
| Compras | 5.2, 5.1 |
| Costos / productos | 5.4, 5.6 (estimado) |
| Pedidos | 5.3 |
| Producción | 5.5–5.7 |
| Pagos | 5.8, 5.10 |
| Gastos / pagos proveedor | 5.9, 5.10 |
| Caja | 5.10 (lectura / efectos vía pagos) |
| Reportes | 5.10 + agregados Stage 9 |
