"""Política Decimal aprobada (Stage 0): ROUND_HALF_UP.

Dinero → 2 decimales; cantidades → 4; porcentajes → 2.
Helper único para Services y Schemas.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from app.core.constants import CANTIDAD_DECIMALES, DINERO_DECIMALES, PORCENTAJE_DECIMALES

_DINERO_QUANT = Decimal("1").scaleb(-DINERO_DECIMALES)
_CANTIDAD_QUANT = Decimal("1").scaleb(-CANTIDAD_DECIMALES)
_PORCENTAJE_QUANT = Decimal("1").scaleb(-PORCENTAJE_DECIMALES)


def a_decimal(valor: Decimal | int | str | float) -> Decimal:
    """Convierte a Decimal sin pasar por float binario cuando es posible."""
    if isinstance(valor, Decimal):
        return valor
    if isinstance(valor, float):
        return Decimal(str(valor))
    return Decimal(valor)


def money_round(valor: Decimal | int | str) -> Decimal:
    """Redondea dinero a 2 decimales (ROUND_HALF_UP)."""
    return a_decimal(valor).quantize(_DINERO_QUANT, rounding=ROUND_HALF_UP)


def qty_round(valor: Decimal | int | str) -> Decimal:
    """Redondea cantidad a 4 decimales (ROUND_HALF_UP)."""
    return a_decimal(valor).quantize(_CANTIDAD_QUANT, rounding=ROUND_HALF_UP)


def percent_round(valor: Decimal | int | str) -> Decimal:
    """Redondea porcentaje a 2 decimales (ROUND_HALF_UP)."""
    return a_decimal(valor).quantize(_PORCENTAJE_QUANT, rounding=ROUND_HALF_UP)


def line_subtotal(cantidad: Decimal, costo_unitario: Decimal) -> Decimal:
    """Subtotal de línea: money_round(qty * unit)."""
    return money_round(qty_round(cantidad) * money_round(costo_unitario))


def costo_promedio_ponderado(
    qty_stock: Decimal,
    costo_viejo: Decimal,
    qty_recepcion: Decimal,
    costo_recepcion: Decimal,
) -> Decimal:
    """Promedio ponderado de materiales (§5.2).

    Si stock previo = 0 → costo unitario de la recepción.
    """
    stock = qty_round(qty_stock)
    recepcion = qty_round(qty_recepcion)
    if recepcion <= 0:
        return money_round(costo_viejo)
    if stock <= 0:
        return money_round(costo_recepcion)
    numerador = (stock * money_round(costo_viejo)) + (
        recepcion * money_round(costo_recepcion)
    )
    return money_round(numerador / (stock + recepcion))
