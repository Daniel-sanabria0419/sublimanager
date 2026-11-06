"""Valores de enums / estados de dominio en español (UPPER_SNAKE).

Fuente: docs/nomenclatura.md y diccionario Stage 0.
Las CHECKs de PostgreSQL usan estos literales; los Services (Stage 3+)
validan contra estas constantes.
"""

from __future__ import annotations

from enum import StrEnum


class TipoProducto(StrEnum):
    FABRICADO = "FABRICADO"
    REVENTA = "REVENTA"
    SERVICIO = "SERVICIO"


class TipoMovimientoInventario(StrEnum):
    COMPRA = "COMPRA"
    PRODUCCION = "PRODUCCION"
    AJUSTE = "AJUSTE"
    DESPERDICIO = "DESPERDICIO"
    DEVOLUCION = "DEVOLUCION"
    TRANSFERENCIA_ENTRADA = "TRANSFERENCIA_ENTRADA"
    TRANSFERENCIA_SALIDA = "TRANSFERENCIA_SALIDA"
    VENTA = "VENTA"
    REVERSO = "REVERSO"


class EstadoMovimientoInventario(StrEnum):
    """Confirmación de movimiento (adición aprobada V1)."""

    BORRADOR = "BORRADOR"
    CONFIRMADO = "CONFIRMADO"
    ANULADO = "ANULADO"


class EstadoPedido(StrEnum):
    PENDIENTE = "PENDIENTE"
    CONFIRMADO = "CONFIRMADO"
    DISENO = "DISENO"
    ESPERANDO_APROBACION = "ESPERANDO_APROBACION"
    EN_PRODUCCION = "EN_PRODUCCION"
    LISTO = "LISTO"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"


class EstadoOrdenProduccion(StrEnum):
    PLANIFICADA = "PLANIFICADA"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADA = "COMPLETADA"
    CANCELADA = "CANCELADA"


class EstadoAprobacionDiseno(StrEnum):
    BORRADOR = "BORRADOR"
    PENDIENTE_APROBACION = "PENDIENTE_APROBACION"
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"


class EstadoPago(StrEnum):
    PENDIENTE = "PENDIENTE"
    CONFIRMADO = "CONFIRMADO"
    ANULADO = "ANULADO"


class EstadoPagoGasto(StrEnum):
    NO_PAGADO = "NO_PAGADO"
    PARCIAL = "PARCIAL"
    PAGADO = "PAGADO"
    ANULADO = "ANULADO"


class EstadoCompra(StrEnum):
    BORRADOR = "BORRADOR"
    RECIBIDA = "RECIBIDA"
    PARCIALMENTE_RECIBIDA = "PARCIALMENTE_RECIBIDA"
    CANCELADA = "CANCELADA"


class TipoCuentaCaja(StrEnum):
    EFECTIVO = "EFECTIVO"
    BANCO = "BANCO"
    BILLETERA_DIGITAL = "BILLETERA_DIGITAL"
    OTRO = "OTRO"


class TipoMovimientoCaja(StrEnum):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"


class TipoCosto(StrEnum):
    MATERIAL = "MATERIAL"
    MANO_OBRA = "MANO_OBRA"
    ELECTRICIDAD = "ELECTRICIDAD"
    DEPRECIACION = "DEPRECIACION"
    MANTENIMIENTO = "MANTENIMIENTO"
    EMPAQUE = "EMPAQUE"
    OTRO = "OTRO"


class EtapaCosto(StrEnum):
    ESTIMADO = "ESTIMADO"
    REAL = "REAL"


def _valores_sql(enum_cls: type[StrEnum]) -> str:
    """Lista literal SQL para CHECK (... IN (...))."""
    return ", ".join(f"'{m.value}'" for m in enum_cls)


# Fragmentos listos para CheckConstraint
IN_TIPO_PRODUCTO = _valores_sql(TipoProducto)
IN_TIPO_MOVIMIENTO_INVENTARIO = _valores_sql(TipoMovimientoInventario)
IN_ESTADO_MOVIMIENTO_INVENTARIO = _valores_sql(EstadoMovimientoInventario)
IN_ESTADO_PEDIDO = _valores_sql(EstadoPedido)
IN_ESTADO_ORDEN_PRODUCCION = _valores_sql(EstadoOrdenProduccion)
IN_ESTADO_APROBACION_DISENO = _valores_sql(EstadoAprobacionDiseno)
IN_ESTADO_PAGO = _valores_sql(EstadoPago)
IN_ESTADO_PAGO_GASTO = _valores_sql(EstadoPagoGasto)
IN_ESTADO_COMPRA = _valores_sql(EstadoCompra)
IN_TIPO_CUENTA_CAJA = _valores_sql(TipoCuentaCaja)
IN_TIPO_MOVIMIENTO_CAJA = _valores_sql(TipoMovimientoCaja)
IN_TIPO_COSTO = _valores_sql(TipoCosto)
IN_ETAPA_COSTO = _valores_sql(EtapaCosto)

# XOR material / variante (existencias, items_movimiento, items_compra)
XOR_MATERIAL_VARIANTE = (
    "(material_id IS NOT NULL AND variante_producto_id IS NULL) OR "
    "(material_id IS NULL AND variante_producto_id IS NOT NULL)"
)

# Exactamente un origen en movimientos_caja
XOR_ORIGEN_MOVIMIENTO_CAJA = (
    "("
    "(CASE WHEN pago_id IS NOT NULL THEN 1 ELSE 0 END) + "
    "(CASE WHEN pago_proveedor_id IS NOT NULL THEN 1 ELSE 0 END) + "
    "(CASE WHEN pago_gasto_id IS NOT NULL THEN 1 ELSE 0 END)"
    ") = 1"
)
