# Manual de usuario — SubliManager V1

Guía operativa para Daniel y operadores del taller. El cliente desktop habla solo con la API; **toda** regla de negocio se aplica en el backend.

## 1. Arranque

1. Asegurar PostgreSQL y la API (`docs/ejecucion.md`).  
2. Ejecutar `python -m desktop.main`.  
3. Verificar en la barra superior: `API · http://127.0.0.1:8000`.

## 2. Menú del desktop

| Sección | Pantallas |
|---------|-----------|
| GENERAL | Dashboard |
| VENTAS | Pedidos, Clientes, Productos |
| PRODUCCIÓN | Órdenes de producción, Recetas, Seguimiento |
| INVENTARIO | Insumos, Productos terminados, Movimientos, Compras, Proveedores |
| FINANZAS | Resumen, Ingresos, Gastos, Cuentas por cobrar/pagar, Caja |
| REPORTES | Listados y exportación CSV/PDF |
| CONFIGURACIÓN | Catálogos auxiliares (métodos de pago, cuentas, etc.) |

Textos de UI en español. Los estados aparecen en `UPPER_SNAKE` (`PENDIENTE`, `EN_PRODUCCION`, …).

## 3. Flujo maestro (vaso / producto FABRICADO)

Escenario validado en QA (Stage 10):

```text
Proveedor → Compra (recibir) → Producto + receta + perfil de costo
  → Cliente → Pedido → (Diseño) → Orden de producción
  → Consumos / cantidades → Completar OP → Pagos → ENTREGADO
  → Reportes / utilidad
```

### 3.1 Inventario y compras

1. **Proveedores** — crear el proveedor.  
2. **Insumos / materiales** — categoría, unidad, `stock_minimo`. El stock inicial, si hace falta, se registra con un movimiento `AJUSTE` (no editando existencias a mano).  
3. **Compras** — crear compra en `BORRADOR` con líneas (material **o** variante).  
4. **Recibir** la compra → genera movimiento `COMPRA`, actualiza `existencias` y `costo_promedio` (promedio ponderado).  
5. Consultar **Movimientos** y alertas de stock bajo.

**Importante:** una compra de inventario **no** es un gasto operativo. Los gastos van en Finanzas → Gastos.

### 3.2 Productos y recetas

1. Crear **categoría** y **producto** con `tipo_producto`:  
   - `FABRICADO` — requiere OP; materiales se descuentan en producción.  
   - `REVENTA` — sin OP; al pasar el pedido a `ENTREGADO` sale stock (si `control_stock`).  
   - `SERVICIO` — sin consumo automático de materiales ni OP por defecto.  
2. **Variantes** (SKU único, precio, talla/color).  
3. **Receta** versionada + ítems (cantidad y `%` desperdicio estimado). Activar la versión vigente.  
4. **Perfil de costo** (mano de obra, electricidad, depreciación, otros). Activar el perfil del alcance.  
5. Consultar **costo estimado** del producto vía API/UI (no recalcular “a ojo” en el cliente).

### 3.3 Clientes y pedidos

1. Alta de **cliente**.  
2. Crear **pedido** con ítems (cantidad, producto/variante).  
   - El sistema congela `precio_venta_unitario`, `costo_unitario_estimado` y `subtotal`.  
   - `descuento` es un **monto** en dinero, no un porcentaje.  
   - Crear/editar el pedido **no** descuenta inventario.  
3. Transiciones de estado (validadas; cada cambio queda en historial):

| Desde | Hacia permitidos |
|-------|------------------|
| `PENDIENTE` | `CONFIRMADO`, `DISENO`, `CANCELADO` |
| `CONFIRMADO` | `DISENO`, `ESPERANDO_APROBACION`, `EN_PRODUCCION`, `LISTO`, `CANCELADO` |
| `DISENO` | `ESPERANDO_APROBACION`, `EN_PRODUCCION`, `CONFIRMADO`, `CANCELADO` |
| `ESPERANDO_APROBACION` | `DISENO`, `EN_PRODUCCION`, `CONFIRMADO`, `CANCELADO` |
| `EN_PRODUCCION` | `LISTO`, `CANCELADO` |
| `LISTO` | `ENTREGADO`, `CANCELADO` |
| `ENTREGADO` / `CANCELADO` | (terminales) |

4. **Diseños** — se registra `ruta_archivo` + versión + estado de aprobación (`BORRADOR` → `PENDIENTE_APROBACION` → `APROBADO` / `RECHAZADO`).  
5. Consultar **saldo** del pedido: `total − pagos CONFIRMADOS`.

### 3.4 Producción

1. Crear **orden de producción** ligada a un `pedido_id` (**obligatorio** en V1) con ítems FABRICADO del pedido. Estado inicial: `PLANIFICADA`.  
2. Revisar **materiales requeridos** (receta activa + disponibilidad en bodega).  
3. **Iniciar** → `EN_PROCESO`.  
4. Registrar **consumos** (productivos y desperdicio real con `es_desperdicio`). Cada consumo confirmado descuenta inventario **una sola vez**.  
5. Actualizar **cantidades** producidas / rechazadas (`producida + rechazada ≤ planificada`). Puede generar entrada de producto terminado.  
6. Cargar **asientos de costo** REAL no materiales (mano de obra, etc.) si aplica.  
7. **Completar** la OP → consolidación de costos REAL; estado `COMPLETADA`.  
8. Comparar **estimado vs real** en la OP / reportes.

Cancelación: solo sin consumos confirmados (reversos de consumo no están en V1).

### 3.5 Finanzas

1. Catálogo: **métodos de pago** y **cuentas de caja** (`EFECTIVO`, `BANCO`, `BILLETERA_DIGITAL`, `OTRO`).  
2. **Pagos de pedido** — anticipos o parciales; al **confirmar** se crea exactamente un `movimientos_caja` `ENTRADA`.  
3. **Gastos** operativos + **pagos de gasto** → caja `SALIDA`.  
4. **Pagos a proveedor** sobre compras → caja `SALIDA`.  
5. Pantallas: resumen, CxC, CxP, caja, ingresos/gastos.

Reconocimiento de **ventas** en reportes: pedidos en estado **`ENTREGADO`** (no cada anticipo).

### 3.6 Reportes y dashboard

- **Dashboard** — KPIs y gráficos desde `/api/v1/reportes/dashboard`.  
- Listados: ventas, productos más vendidos, utilidad, rentabilidad de pedidos, costos de producción, compras, gastos, inventario valorizado, consumos, desperdicios, cuentas pendientes.  
- **Exportación** CSV/PDF de tipos clave (`ventas`, `inventario-valorizado`, `rentabilidad-pedidos`, `resumen-financiero`).

## 4. Buenas prácticas

- No editar `existencias` ni `costo_promedio` directo en la BD.  
- No borrar movimientos de inventario `CONFIRMADO`.  
- Confirmar pagos solo cuando el dinero está recibido; anular genera el reverso de caja correspondiente.  
- Mantener recetas y perfiles como histórico: **activar** una versión nueva, no reescribir la vieja.  
- Resguardar PostgreSQL con regularidad ([`backups.md`](backups.md)).

## 5. Limitaciones conocidas de V1

- No hay OP sin pedido de cliente (`pedido_id` NOT NULL).  
- Entregar un FABRICADO **no** saca automáticamente el producto terminado del stock (solo REVENTA descuenta en `ENTREGADO`).  
- Cancelar OP con consumos ya registrados no está soportado.  
- V1 no incluye autenticación multi-usuario en la API.

## 6. Ayuda técnica

- Instalación: [`instalacion.md`](instalacion.md)  
- API: [`api.md`](api.md) y http://localhost:8000/docs  
- Reglas: [`reglas-negocio.md`](reglas-negocio.md)  
