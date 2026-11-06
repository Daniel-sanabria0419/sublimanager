# Diccionario de datos — extracto Stage 2

Fuente canónica (Project store): `docs/database.md` Stage 0 **APROBADO**.
Este archivo resume lo materializado en migraciones Alembic.

## Convenciones de tipos

| Uso | Tipo |
|-----|------|
| PK | `BIGINT` Identity → `id` |
| Dinero | `NUMERIC(14,2)` |
| Cantidades | `NUMERIC(14,4)` |
| Porcentajes | `NUMERIC(5,2)` |
| Fechas | `TIMESTAMPTZ` |
| Flags | `BOOLEAN` |

## Migraciones

| Revisión | Contenido |
|----------|-----------|
| `20261106_0001` | Stub vacío (Stage 1) |
| `20261106_0002` | 36 tablas + CHECKs / FKs / índices (Stage 2) |

Orden lógico interno de `20261106_0002` (lotes 1–9): catálogos → productos →
materiales → compras/inventario → recetas → pedidos → producción →
gastos/asientos → pagos/caja. Ver docstring de la revisión Alembic.

## Decisiones V1 congeladas

- `ordenes_produccion.pedido_id` **NOT NULL**
- `pedidos.descuento` = **monto** monetario
- `movimientos_inventario.estado` ∈ `BORRADOR \| CONFIRMADO \| ANULADO`
- `movimientos_inventario.grupo_transferencia_id` (UUID, nullable) empareja transferencias
- XOR `material_id` / `variante_producto_id` en `existencias`, `items_movimiento_inventario`, `items_compra`
- `movimientos_caja`: exactamente un origen (`pago_id` XOR `pago_proveedor_id` XOR `pago_gasto_id`)

## Paquetes de modelos

```
backend/app/models/
├── enums.py          # StrEnum UPPER_SNAKE español
├── mixins.py         # helpers PK / timestamps / Numeric
├── inventario/       # módulo A (7)
├── productos/        # módulo B (5)
├── recetas/          # módulo C (4)
├── pedidos/          # módulo D (5)
├── produccion/       # módulo E (4)
├── compras/          # módulo F (3)
└── finanzas/         # módulo G (8)
```

Lista completa de tablas: [`nomenclatura.md`](nomenclatura.md).
