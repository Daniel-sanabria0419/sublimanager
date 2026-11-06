"""Schema de negocio V1 — 36 tablas en español (Stage 2).

Revision ID: 20261106_0002
Revises: 20261106_0001
Create Date: 2026-11-06

Una sola revisión Alembic (más limpia que 10 archivos) que crea las 36
tablas respetando el orden de dependencias. Lotes lógicos documentados:

1. Catálogos: categorias_material, unidades_medida, categorias_producto,
   tecnicas_produccion, clientes, proveedores, metodos_pago, cuentas_caja,
   categorias_gasto, categorias_costo, bodegas
2. Productos: productos, variantes_producto, tecnicas_producto
3. Materiales: materiales
4. Compras e inventario: compras, items_compra, movimientos_inventario,
   items_movimiento_inventario, existencias
5. Recetas y perfiles: recetas_producto, items_receta_producto,
   perfiles_costo_producto
6. Pedidos y diseños: pedidos, items_pedido, disenos_pedido,
   historial_estado_pedido
7. Producción y consumos: ordenes_produccion, items_orden_produccion,
   consumos_produccion
8. Costos de producción: gastos (prereq), asientos_costo_produccion
9. Pagos y finanzas: pagos, pagos_gasto, pagos_proveedor, movimientos_caja

Decisiones V1: pedido_id NOT NULL en OP; descuento=monto; estado +
grupo_transferencia_id en movimientos_inventario.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20261106_0002'
down_revision: Union[str, None] = '20261106_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('bodegas',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('nombre', sa.String(length=120), nullable=False),
    sa.Column('ubicacion', sa.String(length=255), nullable=True),
    sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )
    op.create_table('categorias_costo',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('nombre', sa.String(length=120), nullable=False),
    sa.Column('tipo_costo', sa.String(length=32), nullable=False),
    sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
    sa.CheckConstraint("tipo_costo IN ('MATERIAL', 'MANO_OBRA', 'ELECTRICIDAD', 'DEPRECIACION', 'MANTENIMIENTO', 'EMPAQUE', 'OTRO')", name='ck_categorias_costo_tipo'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )
    op.create_index(op.f('ix_categorias_costo_tipo_costo'), 'categorias_costo', ['tipo_costo'], unique=False)
    op.create_table('categorias_gasto',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('nombre', sa.String(length=120), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=True),
    sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )
    op.create_table('categorias_material',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('nombre', sa.String(length=120), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=True),
    sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )
    op.create_table('categorias_producto',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('nombre', sa.String(length=120), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=True),
    sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )
    op.create_table('clientes',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('nombre', sa.String(length=200), nullable=False),
    sa.Column('identificacion', sa.String(length=64), nullable=True),
    sa.Column('telefono', sa.String(length=40), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('direccion', sa.Text(), nullable=True),
    sa.Column('notas', sa.Text(), nullable=True),
    sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cuentas_caja',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('nombre', sa.String(length=120), nullable=False),
    sa.Column('tipo_cuenta', sa.String(length=32), nullable=False),
    sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
    sa.CheckConstraint("tipo_cuenta IN ('EFECTIVO', 'BANCO', 'BILLETERA_DIGITAL', 'OTRO')", name='ck_cuentas_caja_tipo'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )
    op.create_index(op.f('ix_cuentas_caja_tipo_cuenta'), 'cuentas_caja', ['tipo_cuenta'], unique=False)
    op.create_table('metodos_pago',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('nombre', sa.String(length=80), nullable=False),
    sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )
    op.create_table('proveedores',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('nombre', sa.String(length=200), nullable=False),
    sa.Column('identificacion', sa.String(length=64), nullable=True),
    sa.Column('telefono', sa.String(length=40), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('direccion', sa.Text(), nullable=True),
    sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tecnicas_produccion',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('nombre', sa.String(length=120), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=True),
    sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )
    op.create_table('unidades_medida',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('nombre', sa.String(length=60), nullable=False),
    sa.Column('abreviatura', sa.String(length=16), nullable=False),
    sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )
    op.create_table('compras',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('proveedor_id', sa.BigInteger(), nullable=False),
    sa.Column('fecha_compra', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('numero_factura', sa.String(length=80), nullable=True),
    sa.Column('subtotal', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('total', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('estado', sa.String(length=32), nullable=False),
    sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("estado IN ('BORRADOR', 'RECIBIDA', 'PARCIALMENTE_RECIBIDA', 'CANCELADA')", name='ck_compras_estado'),
    sa.CheckConstraint('subtotal >= 0', name='ck_compras_subtotal_ge_0'),
    sa.CheckConstraint('total >= 0', name='ck_compras_total_ge_0'),
    sa.ForeignKeyConstraint(['proveedor_id'], ['proveedores.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_compras_estado'), 'compras', ['estado'], unique=False)
    op.create_index(op.f('ix_compras_proveedor_id'), 'compras', ['proveedor_id'], unique=False)
    op.create_table('gastos',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('categoria_id', sa.BigInteger(), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=False),
    sa.Column('monto', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('fecha_gasto', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('estado_pago', sa.String(length=32), nullable=False),
    sa.Column('notas', sa.Text(), nullable=True),
    sa.CheckConstraint("estado_pago IN ('NO_PAGADO', 'PARCIAL', 'PAGADO', 'ANULADO')", name='ck_gastos_estado_pago'),
    sa.CheckConstraint('monto > 0', name='ck_gastos_monto_gt_0'),
    sa.ForeignKeyConstraint(['categoria_id'], ['categorias_gasto.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gastos_categoria_id'), 'gastos', ['categoria_id'], unique=False)
    op.create_index(op.f('ix_gastos_estado_pago'), 'gastos', ['estado_pago'], unique=False)
    op.create_table('materiales',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('categoria_id', sa.BigInteger(), nullable=False),
    sa.Column('unidad_id', sa.BigInteger(), nullable=False),
    sa.Column('nombre', sa.String(length=200), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=True),
    sa.Column('stock_minimo', sa.Numeric(precision=14, scale=4), nullable=False),
    sa.Column('costo_promedio', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('costo_promedio >= 0', name='ck_materiales_costo_promedio_ge_0'),
    sa.CheckConstraint('stock_minimo >= 0', name='ck_materiales_stock_minimo_ge_0'),
    sa.ForeignKeyConstraint(['categoria_id'], ['categorias_material.id'], ),
    sa.ForeignKeyConstraint(['unidad_id'], ['unidades_medida.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_materiales_categoria_id'), 'materiales', ['categoria_id'], unique=False)
    op.create_index(op.f('ix_materiales_unidad_id'), 'materiales', ['unidad_id'], unique=False)
    op.create_table('movimientos_inventario',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('tipo_movimiento', sa.String(length=32), nullable=False),
    sa.Column('estado', sa.String(length=16), nullable=False),
    sa.Column('grupo_transferencia_id', sa.UUID(), nullable=True),
    sa.Column('tipo_referencia', sa.String(length=64), nullable=True),
    sa.Column('referencia_id', sa.BigInteger(), nullable=True),
    sa.Column('bodega_id', sa.BigInteger(), nullable=False),
    sa.Column('fecha_movimiento', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('notas', sa.Text(), nullable=True),
    sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("estado IN ('BORRADOR', 'CONFIRMADO', 'ANULADO')", name='ck_movimientos_inventario_estado'),
    sa.CheckConstraint("tipo_movimiento IN ('COMPRA', 'PRODUCCION', 'AJUSTE', 'DESPERDICIO', 'DEVOLUCION', 'TRANSFERENCIA_ENTRADA', 'TRANSFERENCIA_SALIDA', 'VENTA', 'REVERSO')", name='ck_movimientos_inventario_tipo'),
    sa.ForeignKeyConstraint(['bodega_id'], ['bodegas.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_movimientos_inventario_bodega_id'), 'movimientos_inventario', ['bodega_id'], unique=False)
    op.create_index(op.f('ix_movimientos_inventario_estado'), 'movimientos_inventario', ['estado'], unique=False)
    op.create_index(op.f('ix_movimientos_inventario_grupo_transferencia_id'), 'movimientos_inventario', ['grupo_transferencia_id'], unique=False)
    op.create_index(op.f('ix_movimientos_inventario_tipo_movimiento'), 'movimientos_inventario', ['tipo_movimiento'], unique=False)
    op.create_table('pedidos',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('numero_pedido', sa.String(length=40), nullable=False),
    sa.Column('cliente_id', sa.BigInteger(), nullable=False),
    sa.Column('fecha_pedido', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('fecha_entrega', sa.DateTime(timezone=True), nullable=True),
    sa.Column('subtotal', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('descuento', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('total', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('estado', sa.String(length=32), nullable=False),
    sa.Column('notas', sa.Text(), nullable=True),
    sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("estado IN ('PENDIENTE', 'CONFIRMADO', 'DISENO', 'ESPERANDO_APROBACION', 'EN_PRODUCCION', 'LISTO', 'ENTREGADO', 'CANCELADO')", name='ck_pedidos_estado'),
    sa.CheckConstraint('descuento >= 0', name='ck_pedidos_descuento_ge_0'),
    sa.CheckConstraint('subtotal >= 0', name='ck_pedidos_subtotal_ge_0'),
    sa.CheckConstraint('total >= 0', name='ck_pedidos_total_ge_0'),
    sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('numero_pedido')
    )
    op.create_index(op.f('ix_pedidos_cliente_id'), 'pedidos', ['cliente_id'], unique=False)
    op.create_index(op.f('ix_pedidos_estado'), 'pedidos', ['estado'], unique=False)
    op.create_table('productos',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('categoria_id', sa.BigInteger(), nullable=False),
    sa.Column('nombre', sa.String(length=200), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=True),
    sa.Column('tipo_producto', sa.String(length=32), nullable=False),
    sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("tipo_producto IN ('FABRICADO', 'REVENTA', 'SERVICIO')", name='ck_productos_tipo_producto'),
    sa.ForeignKeyConstraint(['categoria_id'], ['categorias_producto.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_productos_categoria_id'), 'productos', ['categoria_id'], unique=False)
    op.create_index(op.f('ix_productos_tipo_producto'), 'productos', ['tipo_producto'], unique=False)
    op.create_table('historial_estado_pedido',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('pedido_id', sa.BigInteger(), nullable=False),
    sa.Column('estado_anterior', sa.String(length=32), nullable=True),
    sa.Column('estado_nuevo', sa.String(length=32), nullable=False),
    sa.Column('cambiado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('notas', sa.Text(), nullable=True),
    sa.CheckConstraint("estado_anterior IS NULL OR estado_anterior IN ('PENDIENTE', 'CONFIRMADO', 'DISENO', 'ESPERANDO_APROBACION', 'EN_PRODUCCION', 'LISTO', 'ENTREGADO', 'CANCELADO')", name='ck_historial_estado_anterior'),
    sa.CheckConstraint("estado_nuevo IN ('PENDIENTE', 'CONFIRMADO', 'DISENO', 'ESPERANDO_APROBACION', 'EN_PRODUCCION', 'LISTO', 'ENTREGADO', 'CANCELADO')", name='ck_historial_estado_nuevo'),
    sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_historial_estado_pedido_pedido_id'), 'historial_estado_pedido', ['pedido_id'], unique=False)
    op.create_table('ordenes_produccion',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('pedido_id', sa.BigInteger(), nullable=False),
    sa.Column('numero_produccion', sa.String(length=40), nullable=False),
    sa.Column('estado', sa.String(length=32), nullable=False),
    sa.Column('fecha_inicio', sa.DateTime(timezone=True), nullable=True),
    sa.Column('fecha_fin', sa.DateTime(timezone=True), nullable=True),
    sa.Column('notas', sa.Text(), nullable=True),
    sa.CheckConstraint("estado IN ('PLANIFICADA', 'EN_PROCESO', 'COMPLETADA', 'CANCELADA')", name='ck_ordenes_produccion_estado'),
    sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('numero_produccion')
    )
    op.create_index(op.f('ix_ordenes_produccion_estado'), 'ordenes_produccion', ['estado'], unique=False)
    op.create_index(op.f('ix_ordenes_produccion_pedido_id'), 'ordenes_produccion', ['pedido_id'], unique=False)
    op.create_table('pagos',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('pedido_id', sa.BigInteger(), nullable=False),
    sa.Column('metodo_pago_id', sa.BigInteger(), nullable=False),
    sa.Column('cuenta_caja_id', sa.BigInteger(), nullable=False),
    sa.Column('monto', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('fecha_pago', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('referencia', sa.String(length=120), nullable=True),
    sa.Column('estado', sa.String(length=32), nullable=False),
    sa.Column('notas', sa.Text(), nullable=True),
    sa.CheckConstraint("estado IN ('PENDIENTE', 'CONFIRMADO', 'ANULADO')", name='ck_pagos_estado'),
    sa.CheckConstraint('monto > 0', name='ck_pagos_monto_gt_0'),
    sa.ForeignKeyConstraint(['cuenta_caja_id'], ['cuentas_caja.id'], ),
    sa.ForeignKeyConstraint(['metodo_pago_id'], ['metodos_pago.id'], ),
    sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pagos_cuenta_caja_id'), 'pagos', ['cuenta_caja_id'], unique=False)
    op.create_index(op.f('ix_pagos_estado'), 'pagos', ['estado'], unique=False)
    op.create_index(op.f('ix_pagos_metodo_pago_id'), 'pagos', ['metodo_pago_id'], unique=False)
    op.create_index(op.f('ix_pagos_pedido_id'), 'pagos', ['pedido_id'], unique=False)
    op.create_table('pagos_gasto',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('gasto_id', sa.BigInteger(), nullable=False),
    sa.Column('metodo_pago_id', sa.BigInteger(), nullable=False),
    sa.Column('cuenta_caja_id', sa.BigInteger(), nullable=False),
    sa.Column('monto', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('fecha_pago', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('estado', sa.String(length=32), nullable=False),
    sa.Column('referencia', sa.String(length=120), nullable=True),
    sa.CheckConstraint("estado IN ('PENDIENTE', 'CONFIRMADO', 'ANULADO')", name='ck_pagos_gasto_estado'),
    sa.CheckConstraint('monto > 0', name='ck_pagos_gasto_monto_gt_0'),
    sa.ForeignKeyConstraint(['cuenta_caja_id'], ['cuentas_caja.id'], ),
    sa.ForeignKeyConstraint(['gasto_id'], ['gastos.id'], ),
    sa.ForeignKeyConstraint(['metodo_pago_id'], ['metodos_pago.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pagos_gasto_cuenta_caja_id'), 'pagos_gasto', ['cuenta_caja_id'], unique=False)
    op.create_index(op.f('ix_pagos_gasto_estado'), 'pagos_gasto', ['estado'], unique=False)
    op.create_index(op.f('ix_pagos_gasto_gasto_id'), 'pagos_gasto', ['gasto_id'], unique=False)
    op.create_index(op.f('ix_pagos_gasto_metodo_pago_id'), 'pagos_gasto', ['metodo_pago_id'], unique=False)
    op.create_table('pagos_proveedor',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('compra_id', sa.BigInteger(), nullable=False),
    sa.Column('metodo_pago_id', sa.BigInteger(), nullable=False),
    sa.Column('cuenta_caja_id', sa.BigInteger(), nullable=False),
    sa.Column('monto', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('fecha_pago', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('estado', sa.String(length=32), nullable=False),
    sa.Column('referencia', sa.String(length=120), nullable=True),
    sa.CheckConstraint("estado IN ('PENDIENTE', 'CONFIRMADO', 'ANULADO')", name='ck_pagos_proveedor_estado'),
    sa.CheckConstraint('monto > 0', name='ck_pagos_proveedor_monto_gt_0'),
    sa.ForeignKeyConstraint(['compra_id'], ['compras.id'], ),
    sa.ForeignKeyConstraint(['cuenta_caja_id'], ['cuentas_caja.id'], ),
    sa.ForeignKeyConstraint(['metodo_pago_id'], ['metodos_pago.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pagos_proveedor_compra_id'), 'pagos_proveedor', ['compra_id'], unique=False)
    op.create_index(op.f('ix_pagos_proveedor_cuenta_caja_id'), 'pagos_proveedor', ['cuenta_caja_id'], unique=False)
    op.create_index(op.f('ix_pagos_proveedor_estado'), 'pagos_proveedor', ['estado'], unique=False)
    op.create_index(op.f('ix_pagos_proveedor_metodo_pago_id'), 'pagos_proveedor', ['metodo_pago_id'], unique=False)
    op.create_table('tecnicas_producto',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('producto_id', sa.BigInteger(), nullable=False),
    sa.Column('tecnica_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['producto_id'], ['productos.id'], ),
    sa.ForeignKeyConstraint(['tecnica_id'], ['tecnicas_produccion.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('producto_id', 'tecnica_id', name='uq_tecnicas_producto_par')
    )
    op.create_index(op.f('ix_tecnicas_producto_producto_id'), 'tecnicas_producto', ['producto_id'], unique=False)
    op.create_index(op.f('ix_tecnicas_producto_tecnica_id'), 'tecnicas_producto', ['tecnica_id'], unique=False)
    op.create_table('variantes_producto',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('producto_id', sa.BigInteger(), nullable=False),
    sa.Column('sku', sa.String(length=64), nullable=False),
    sa.Column('talla', sa.String(length=64), nullable=True),
    sa.Column('color', sa.String(length=64), nullable=True),
    sa.Column('precio_venta', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('control_stock', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
    sa.CheckConstraint('precio_venta >= 0', name='ck_variantes_precio_venta_ge_0'),
    sa.ForeignKeyConstraint(['producto_id'], ['productos.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('sku')
    )
    op.create_index(op.f('ix_variantes_producto_producto_id'), 'variantes_producto', ['producto_id'], unique=False)
    op.create_table('existencias',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('bodega_id', sa.BigInteger(), nullable=False),
    sa.Column('material_id', sa.BigInteger(), nullable=True),
    sa.Column('variante_producto_id', sa.BigInteger(), nullable=True),
    sa.Column('cantidad', sa.Numeric(precision=14, scale=4), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('(material_id IS NOT NULL AND variante_producto_id IS NULL) OR (material_id IS NULL AND variante_producto_id IS NOT NULL)', name='ck_existencias_xor_articulo'),
    sa.CheckConstraint('cantidad >= 0', name='ck_existencias_cantidad_ge_0'),
    sa.ForeignKeyConstraint(['bodega_id'], ['bodegas.id'], ),
    sa.ForeignKeyConstraint(['material_id'], ['materiales.id'], ),
    sa.ForeignKeyConstraint(['variante_producto_id'], ['variantes_producto.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_existencias_bodega_id'), 'existencias', ['bodega_id'], unique=False)
    op.create_index(op.f('ix_existencias_material_id'), 'existencias', ['material_id'], unique=False)
    op.create_index(op.f('ix_existencias_variante_producto_id'), 'existencias', ['variante_producto_id'], unique=False)
    op.create_index('uq_existencias_bodega_material', 'existencias', ['bodega_id', 'material_id'], unique=True, postgresql_where='material_id IS NOT NULL')
    op.create_index('uq_existencias_bodega_variante', 'existencias', ['bodega_id', 'variante_producto_id'], unique=True, postgresql_where='variante_producto_id IS NOT NULL')
    op.create_table('items_compra',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('compra_id', sa.BigInteger(), nullable=False),
    sa.Column('material_id', sa.BigInteger(), nullable=True),
    sa.Column('variante_producto_id', sa.BigInteger(), nullable=True),
    sa.Column('cantidad', sa.Numeric(precision=14, scale=4), nullable=False),
    sa.Column('costo_unitario', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('subtotal', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.CheckConstraint('(material_id IS NOT NULL AND variante_producto_id IS NULL) OR (material_id IS NULL AND variante_producto_id IS NOT NULL)', name='ck_items_compra_xor_articulo'),
    sa.CheckConstraint('cantidad > 0', name='ck_items_compra_cantidad_gt_0'),
    sa.CheckConstraint('costo_unitario >= 0', name='ck_items_compra_costo_ge_0'),
    sa.CheckConstraint('subtotal >= 0', name='ck_items_compra_subtotal_ge_0'),
    sa.ForeignKeyConstraint(['compra_id'], ['compras.id'], ),
    sa.ForeignKeyConstraint(['material_id'], ['materiales.id'], ),
    sa.ForeignKeyConstraint(['variante_producto_id'], ['variantes_producto.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_items_compra_compra_id'), 'items_compra', ['compra_id'], unique=False)
    op.create_index(op.f('ix_items_compra_material_id'), 'items_compra', ['material_id'], unique=False)
    op.create_index(op.f('ix_items_compra_variante_producto_id'), 'items_compra', ['variante_producto_id'], unique=False)
    op.create_table('items_movimiento_inventario',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('movimiento_id', sa.BigInteger(), nullable=False),
    sa.Column('material_id', sa.BigInteger(), nullable=True),
    sa.Column('variante_producto_id', sa.BigInteger(), nullable=True),
    sa.Column('cantidad', sa.Numeric(precision=14, scale=4), nullable=False),
    sa.Column('costo_unitario', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('costo_total', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.CheckConstraint('(material_id IS NOT NULL AND variante_producto_id IS NULL) OR (material_id IS NULL AND variante_producto_id IS NOT NULL)', name='ck_items_movimiento_xor_articulo'),
    sa.CheckConstraint('cantidad > 0', name='ck_items_movimiento_cantidad_gt_0'),
    sa.CheckConstraint('costo_total >= 0', name='ck_items_movimiento_costo_total_ge_0'),
    sa.CheckConstraint('costo_unitario >= 0', name='ck_items_movimiento_costo_unitario_ge_0'),
    sa.ForeignKeyConstraint(['material_id'], ['materiales.id'], ),
    sa.ForeignKeyConstraint(['movimiento_id'], ['movimientos_inventario.id'], ),
    sa.ForeignKeyConstraint(['variante_producto_id'], ['variantes_producto.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_items_movimiento_inventario_material_id'), 'items_movimiento_inventario', ['material_id'], unique=False)
    op.create_index(op.f('ix_items_movimiento_inventario_movimiento_id'), 'items_movimiento_inventario', ['movimiento_id'], unique=False)
    op.create_index(op.f('ix_items_movimiento_inventario_variante_producto_id'), 'items_movimiento_inventario', ['variante_producto_id'], unique=False)
    op.create_table('items_pedido',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('pedido_id', sa.BigInteger(), nullable=False),
    sa.Column('producto_id', sa.BigInteger(), nullable=False),
    sa.Column('variante_id', sa.BigInteger(), nullable=True),
    sa.Column('descripcion', sa.Text(), nullable=True),
    sa.Column('cantidad', sa.Numeric(precision=14, scale=4), nullable=False),
    sa.Column('precio_venta_unitario', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('costo_unitario_estimado', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('subtotal', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.CheckConstraint('cantidad > 0', name='ck_items_pedido_cantidad_gt_0'),
    sa.CheckConstraint('costo_unitario_estimado >= 0', name='ck_items_pedido_costo_est_ge_0'),
    sa.CheckConstraint('precio_venta_unitario >= 0', name='ck_items_pedido_precio_ge_0'),
    sa.CheckConstraint('subtotal >= 0', name='ck_items_pedido_subtotal_ge_0'),
    sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id'], ),
    sa.ForeignKeyConstraint(['producto_id'], ['productos.id'], ),
    sa.ForeignKeyConstraint(['variante_id'], ['variantes_producto.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_items_pedido_pedido_id'), 'items_pedido', ['pedido_id'], unique=False)
    op.create_index(op.f('ix_items_pedido_producto_id'), 'items_pedido', ['producto_id'], unique=False)
    op.create_index(op.f('ix_items_pedido_variante_id'), 'items_pedido', ['variante_id'], unique=False)
    op.create_table('movimientos_caja',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('cuenta_caja_id', sa.BigInteger(), nullable=False),
    sa.Column('tipo_movimiento', sa.String(length=32), nullable=False),
    sa.Column('monto', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('pago_id', sa.BigInteger(), nullable=True),
    sa.Column('pago_proveedor_id', sa.BigInteger(), nullable=True),
    sa.Column('pago_gasto_id', sa.BigInteger(), nullable=True),
    sa.Column('fecha_movimiento', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=True),
    sa.CheckConstraint("tipo_movimiento IN ('ENTRADA', 'SALIDA')", name='ck_movimientos_caja_tipo'),
    sa.CheckConstraint('((CASE WHEN pago_id IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN pago_proveedor_id IS NOT NULL THEN 1 ELSE 0 END) + (CASE WHEN pago_gasto_id IS NOT NULL THEN 1 ELSE 0 END)) = 1', name='ck_movimientos_caja_un_origen'),
    sa.CheckConstraint('monto > 0', name='ck_movimientos_caja_monto_gt_0'),
    sa.ForeignKeyConstraint(['cuenta_caja_id'], ['cuentas_caja.id'], ),
    sa.ForeignKeyConstraint(['pago_gasto_id'], ['pagos_gasto.id'], ),
    sa.ForeignKeyConstraint(['pago_id'], ['pagos.id'], ),
    sa.ForeignKeyConstraint(['pago_proveedor_id'], ['pagos_proveedor.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_movimientos_caja_cuenta_caja_id'), 'movimientos_caja', ['cuenta_caja_id'], unique=False)
    op.create_index(op.f('ix_movimientos_caja_tipo_movimiento'), 'movimientos_caja', ['tipo_movimiento'], unique=False)
    op.create_index('uq_movimientos_caja_pago_gasto_id', 'movimientos_caja', ['pago_gasto_id'], unique=True, postgresql_where='pago_gasto_id IS NOT NULL')
    op.create_index('uq_movimientos_caja_pago_id', 'movimientos_caja', ['pago_id'], unique=True, postgresql_where='pago_id IS NOT NULL')
    op.create_index('uq_movimientos_caja_pago_proveedor_id', 'movimientos_caja', ['pago_proveedor_id'], unique=True, postgresql_where='pago_proveedor_id IS NOT NULL')
    op.create_table('perfiles_costo_producto',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('producto_id', sa.BigInteger(), nullable=False),
    sa.Column('variante_id', sa.BigInteger(), nullable=True),
    sa.Column('costo_mano_obra_por_unidad', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('costo_electricidad_por_unidad', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('costo_depreciacion_por_unidad', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('costo_otros_por_unidad', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('vigente_desde', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
    sa.CheckConstraint('costo_depreciacion_por_unidad >= 0', name='ck_perfiles_costo_depreciacion_ge_0'),
    sa.CheckConstraint('costo_electricidad_por_unidad >= 0', name='ck_perfiles_costo_electricidad_ge_0'),
    sa.CheckConstraint('costo_mano_obra_por_unidad >= 0', name='ck_perfiles_costo_mano_obra_ge_0'),
    sa.CheckConstraint('costo_otros_por_unidad >= 0', name='ck_perfiles_costo_otros_ge_0'),
    sa.ForeignKeyConstraint(['producto_id'], ['productos.id'], ),
    sa.ForeignKeyConstraint(['variante_id'], ['variantes_producto.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_perfiles_costo_producto_producto_id'), 'perfiles_costo_producto', ['producto_id'], unique=False)
    op.create_index(op.f('ix_perfiles_costo_producto_variante_id'), 'perfiles_costo_producto', ['variante_id'], unique=False)
    op.create_table('recetas_producto',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('producto_id', sa.BigInteger(), nullable=False),
    sa.Column('variante_id', sa.BigInteger(), nullable=True),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(length=120), nullable=False),
    sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['producto_id'], ['productos.id'], ),
    sa.ForeignKeyConstraint(['variante_id'], ['variantes_producto.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recetas_producto_producto_id'), 'recetas_producto', ['producto_id'], unique=False)
    op.create_index(op.f('ix_recetas_producto_variante_id'), 'recetas_producto', ['variante_id'], unique=False)
    op.create_index('uq_recetas_producto_con_variante', 'recetas_producto', ['producto_id', 'variante_id', 'version'], unique=True, postgresql_where='variante_id IS NOT NULL')
    op.create_index('uq_recetas_producto_sin_variante', 'recetas_producto', ['producto_id', 'version'], unique=True, postgresql_where='variante_id IS NULL')
    op.create_table('disenos_pedido',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('item_pedido_id', sa.BigInteger(), nullable=False),
    sa.Column('ruta_archivo', sa.String(length=1024), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('estado_aprobacion', sa.String(length=32), nullable=False),
    sa.Column('notas', sa.Text(), nullable=True),
    sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("estado_aprobacion IN ('BORRADOR', 'PENDIENTE_APROBACION', 'APROBADO', 'RECHAZADO')", name='ck_disenos_pedido_estado_aprobacion'),
    sa.CheckConstraint('version > 0', name='ck_disenos_pedido_version_gt_0'),
    sa.ForeignKeyConstraint(['item_pedido_id'], ['items_pedido.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_disenos_pedido_estado_aprobacion'), 'disenos_pedido', ['estado_aprobacion'], unique=False)
    op.create_index(op.f('ix_disenos_pedido_item_pedido_id'), 'disenos_pedido', ['item_pedido_id'], unique=False)
    op.create_table('items_orden_produccion',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('orden_produccion_id', sa.BigInteger(), nullable=False),
    sa.Column('item_pedido_id', sa.BigInteger(), nullable=False),
    sa.Column('cantidad_planificada', sa.Numeric(precision=14, scale=4), nullable=False),
    sa.Column('cantidad_producida', sa.Numeric(precision=14, scale=4), nullable=False),
    sa.Column('cantidad_rechazada', sa.Numeric(precision=14, scale=4), nullable=False),
    sa.CheckConstraint('cantidad_planificada > 0', name='ck_items_op_planificada_gt_0'),
    sa.CheckConstraint('cantidad_producida + cantidad_rechazada <= cantidad_planificada', name='ck_items_op_cantidades_coherentes'),
    sa.CheckConstraint('cantidad_producida >= 0', name='ck_items_op_producida_ge_0'),
    sa.CheckConstraint('cantidad_rechazada >= 0', name='ck_items_op_rechazada_ge_0'),
    sa.ForeignKeyConstraint(['item_pedido_id'], ['items_pedido.id'], ),
    sa.ForeignKeyConstraint(['orden_produccion_id'], ['ordenes_produccion.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_items_orden_produccion_item_pedido_id'), 'items_orden_produccion', ['item_pedido_id'], unique=False)
    op.create_index(op.f('ix_items_orden_produccion_orden_produccion_id'), 'items_orden_produccion', ['orden_produccion_id'], unique=False)
    op.create_table('items_receta_producto',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('receta_id', sa.BigInteger(), nullable=False),
    sa.Column('material_id', sa.BigInteger(), nullable=False),
    sa.Column('cantidad', sa.Numeric(precision=14, scale=4), nullable=False),
    sa.Column('porcentaje_desperdicio', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('notas', sa.Text(), nullable=True),
    sa.CheckConstraint('cantidad > 0', name='ck_items_receta_cantidad_gt_0'),
    sa.CheckConstraint('porcentaje_desperdicio >= 0', name='ck_items_receta_desperdicio_ge_0'),
    sa.ForeignKeyConstraint(['material_id'], ['materiales.id'], ),
    sa.ForeignKeyConstraint(['receta_id'], ['recetas_producto.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_items_receta_producto_material_id'), 'items_receta_producto', ['material_id'], unique=False)
    op.create_index(op.f('ix_items_receta_producto_receta_id'), 'items_receta_producto', ['receta_id'], unique=False)
    op.create_table('asientos_costo_produccion',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('item_orden_produccion_id', sa.BigInteger(), nullable=False),
    sa.Column('categoria_costo_id', sa.BigInteger(), nullable=False),
    sa.Column('gasto_id', sa.BigInteger(), nullable=True),
    sa.Column('descripcion', sa.Text(), nullable=True),
    sa.Column('etapa_costo', sa.String(length=16), nullable=False),
    sa.Column('cantidad', sa.Numeric(precision=14, scale=4), nullable=False),
    sa.Column('costo_unitario', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('costo_total', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("etapa_costo IN ('ESTIMADO', 'REAL')", name='ck_asientos_costo_etapa'),
    sa.CheckConstraint('cantidad >= 0', name='ck_asientos_costo_cantidad_ge_0'),
    sa.CheckConstraint('costo_total >= 0', name='ck_asientos_costo_total_ge_0'),
    sa.CheckConstraint('costo_unitario >= 0', name='ck_asientos_costo_unitario_ge_0'),
    sa.ForeignKeyConstraint(['categoria_costo_id'], ['categorias_costo.id'], ),
    sa.ForeignKeyConstraint(['gasto_id'], ['gastos.id'], ),
    sa.ForeignKeyConstraint(['item_orden_produccion_id'], ['items_orden_produccion.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_asientos_costo_produccion_categoria_costo_id'), 'asientos_costo_produccion', ['categoria_costo_id'], unique=False)
    op.create_index(op.f('ix_asientos_costo_produccion_etapa_costo'), 'asientos_costo_produccion', ['etapa_costo'], unique=False)
    op.create_index(op.f('ix_asientos_costo_produccion_gasto_id'), 'asientos_costo_produccion', ['gasto_id'], unique=False)
    op.create_index(op.f('ix_asientos_costo_produccion_item_orden_produccion_id'), 'asientos_costo_produccion', ['item_orden_produccion_id'], unique=False)
    op.create_table('consumos_produccion',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('item_orden_produccion_id', sa.BigInteger(), nullable=False),
    sa.Column('material_id', sa.BigInteger(), nullable=False),
    sa.Column('cantidad_consumida', sa.Numeric(precision=14, scale=4), nullable=False),
    sa.Column('costo_unitario_snapshot', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('costo_total', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('consumido_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('es_desperdicio', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('notas', sa.Text(), nullable=True),
    sa.CheckConstraint('cantidad_consumida > 0', name='ck_consumos_cantidad_gt_0'),
    sa.CheckConstraint('costo_total >= 0', name='ck_consumos_costo_total_ge_0'),
    sa.CheckConstraint('costo_unitario_snapshot >= 0', name='ck_consumos_costo_unitario_ge_0'),
    sa.ForeignKeyConstraint(['item_orden_produccion_id'], ['items_orden_produccion.id'], ),
    sa.ForeignKeyConstraint(['material_id'], ['materiales.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consumos_produccion_item_orden_produccion_id'), 'consumos_produccion', ['item_orden_produccion_id'], unique=False)
    op.create_index(op.f('ix_consumos_produccion_material_id'), 'consumos_produccion', ['material_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_consumos_produccion_material_id'), table_name='consumos_produccion')
    op.drop_index(op.f('ix_consumos_produccion_item_orden_produccion_id'), table_name='consumos_produccion')
    op.drop_table('consumos_produccion')
    op.drop_index(op.f('ix_asientos_costo_produccion_item_orden_produccion_id'), table_name='asientos_costo_produccion')
    op.drop_index(op.f('ix_asientos_costo_produccion_gasto_id'), table_name='asientos_costo_produccion')
    op.drop_index(op.f('ix_asientos_costo_produccion_etapa_costo'), table_name='asientos_costo_produccion')
    op.drop_index(op.f('ix_asientos_costo_produccion_categoria_costo_id'), table_name='asientos_costo_produccion')
    op.drop_table('asientos_costo_produccion')
    op.drop_index(op.f('ix_items_receta_producto_receta_id'), table_name='items_receta_producto')
    op.drop_index(op.f('ix_items_receta_producto_material_id'), table_name='items_receta_producto')
    op.drop_table('items_receta_producto')
    op.drop_index(op.f('ix_items_orden_produccion_orden_produccion_id'), table_name='items_orden_produccion')
    op.drop_index(op.f('ix_items_orden_produccion_item_pedido_id'), table_name='items_orden_produccion')
    op.drop_table('items_orden_produccion')
    op.drop_index(op.f('ix_disenos_pedido_item_pedido_id'), table_name='disenos_pedido')
    op.drop_index(op.f('ix_disenos_pedido_estado_aprobacion'), table_name='disenos_pedido')
    op.drop_table('disenos_pedido')
    op.drop_index('uq_recetas_producto_sin_variante', table_name='recetas_producto', postgresql_where='variante_id IS NULL')
    op.drop_index('uq_recetas_producto_con_variante', table_name='recetas_producto', postgresql_where='variante_id IS NOT NULL')
    op.drop_index(op.f('ix_recetas_producto_variante_id'), table_name='recetas_producto')
    op.drop_index(op.f('ix_recetas_producto_producto_id'), table_name='recetas_producto')
    op.drop_table('recetas_producto')
    op.drop_index(op.f('ix_perfiles_costo_producto_variante_id'), table_name='perfiles_costo_producto')
    op.drop_index(op.f('ix_perfiles_costo_producto_producto_id'), table_name='perfiles_costo_producto')
    op.drop_table('perfiles_costo_producto')
    op.drop_index('uq_movimientos_caja_pago_proveedor_id', table_name='movimientos_caja', postgresql_where='pago_proveedor_id IS NOT NULL')
    op.drop_index('uq_movimientos_caja_pago_id', table_name='movimientos_caja', postgresql_where='pago_id IS NOT NULL')
    op.drop_index('uq_movimientos_caja_pago_gasto_id', table_name='movimientos_caja', postgresql_where='pago_gasto_id IS NOT NULL')
    op.drop_index(op.f('ix_movimientos_caja_tipo_movimiento'), table_name='movimientos_caja')
    op.drop_index(op.f('ix_movimientos_caja_cuenta_caja_id'), table_name='movimientos_caja')
    op.drop_table('movimientos_caja')
    op.drop_index(op.f('ix_items_pedido_variante_id'), table_name='items_pedido')
    op.drop_index(op.f('ix_items_pedido_producto_id'), table_name='items_pedido')
    op.drop_index(op.f('ix_items_pedido_pedido_id'), table_name='items_pedido')
    op.drop_table('items_pedido')
    op.drop_index(op.f('ix_items_movimiento_inventario_variante_producto_id'), table_name='items_movimiento_inventario')
    op.drop_index(op.f('ix_items_movimiento_inventario_movimiento_id'), table_name='items_movimiento_inventario')
    op.drop_index(op.f('ix_items_movimiento_inventario_material_id'), table_name='items_movimiento_inventario')
    op.drop_table('items_movimiento_inventario')
    op.drop_index(op.f('ix_items_compra_variante_producto_id'), table_name='items_compra')
    op.drop_index(op.f('ix_items_compra_material_id'), table_name='items_compra')
    op.drop_index(op.f('ix_items_compra_compra_id'), table_name='items_compra')
    op.drop_table('items_compra')
    op.drop_index('uq_existencias_bodega_variante', table_name='existencias', postgresql_where='variante_producto_id IS NOT NULL')
    op.drop_index('uq_existencias_bodega_material', table_name='existencias', postgresql_where='material_id IS NOT NULL')
    op.drop_index(op.f('ix_existencias_variante_producto_id'), table_name='existencias')
    op.drop_index(op.f('ix_existencias_material_id'), table_name='existencias')
    op.drop_index(op.f('ix_existencias_bodega_id'), table_name='existencias')
    op.drop_table('existencias')
    op.drop_index(op.f('ix_variantes_producto_producto_id'), table_name='variantes_producto')
    op.drop_table('variantes_producto')
    op.drop_index(op.f('ix_tecnicas_producto_tecnica_id'), table_name='tecnicas_producto')
    op.drop_index(op.f('ix_tecnicas_producto_producto_id'), table_name='tecnicas_producto')
    op.drop_table('tecnicas_producto')
    op.drop_index(op.f('ix_pagos_proveedor_metodo_pago_id'), table_name='pagos_proveedor')
    op.drop_index(op.f('ix_pagos_proveedor_estado'), table_name='pagos_proveedor')
    op.drop_index(op.f('ix_pagos_proveedor_cuenta_caja_id'), table_name='pagos_proveedor')
    op.drop_index(op.f('ix_pagos_proveedor_compra_id'), table_name='pagos_proveedor')
    op.drop_table('pagos_proveedor')
    op.drop_index(op.f('ix_pagos_gasto_metodo_pago_id'), table_name='pagos_gasto')
    op.drop_index(op.f('ix_pagos_gasto_gasto_id'), table_name='pagos_gasto')
    op.drop_index(op.f('ix_pagos_gasto_estado'), table_name='pagos_gasto')
    op.drop_index(op.f('ix_pagos_gasto_cuenta_caja_id'), table_name='pagos_gasto')
    op.drop_table('pagos_gasto')
    op.drop_index(op.f('ix_pagos_pedido_id'), table_name='pagos')
    op.drop_index(op.f('ix_pagos_metodo_pago_id'), table_name='pagos')
    op.drop_index(op.f('ix_pagos_estado'), table_name='pagos')
    op.drop_index(op.f('ix_pagos_cuenta_caja_id'), table_name='pagos')
    op.drop_table('pagos')
    op.drop_index(op.f('ix_ordenes_produccion_pedido_id'), table_name='ordenes_produccion')
    op.drop_index(op.f('ix_ordenes_produccion_estado'), table_name='ordenes_produccion')
    op.drop_table('ordenes_produccion')
    op.drop_index(op.f('ix_historial_estado_pedido_pedido_id'), table_name='historial_estado_pedido')
    op.drop_table('historial_estado_pedido')
    op.drop_index(op.f('ix_productos_tipo_producto'), table_name='productos')
    op.drop_index(op.f('ix_productos_categoria_id'), table_name='productos')
    op.drop_table('productos')
    op.drop_index(op.f('ix_pedidos_estado'), table_name='pedidos')
    op.drop_index(op.f('ix_pedidos_cliente_id'), table_name='pedidos')
    op.drop_table('pedidos')
    op.drop_index(op.f('ix_movimientos_inventario_tipo_movimiento'), table_name='movimientos_inventario')
    op.drop_index(op.f('ix_movimientos_inventario_grupo_transferencia_id'), table_name='movimientos_inventario')
    op.drop_index(op.f('ix_movimientos_inventario_estado'), table_name='movimientos_inventario')
    op.drop_index(op.f('ix_movimientos_inventario_bodega_id'), table_name='movimientos_inventario')
    op.drop_table('movimientos_inventario')
    op.drop_index(op.f('ix_materiales_unidad_id'), table_name='materiales')
    op.drop_index(op.f('ix_materiales_categoria_id'), table_name='materiales')
    op.drop_table('materiales')
    op.drop_index(op.f('ix_gastos_estado_pago'), table_name='gastos')
    op.drop_index(op.f('ix_gastos_categoria_id'), table_name='gastos')
    op.drop_table('gastos')
    op.drop_index(op.f('ix_compras_proveedor_id'), table_name='compras')
    op.drop_index(op.f('ix_compras_estado'), table_name='compras')
    op.drop_table('compras')
    op.drop_table('unidades_medida')
    op.drop_table('tecnicas_produccion')
    op.drop_table('proveedores')
    op.drop_table('metodos_pago')
    op.drop_index(op.f('ix_cuentas_caja_tipo_cuenta'), table_name='cuentas_caja')
    op.drop_table('cuentas_caja')
    op.drop_table('clientes')
    op.drop_table('categorias_producto')
    op.drop_table('categorias_material')
    op.drop_table('categorias_gasto')
    op.drop_index(op.f('ix_categorias_costo_tipo_costo'), table_name='categorias_costo')
    op.drop_table('categorias_costo')
    op.drop_table('bodegas')
