"""Tests unitarios de la política Decimal (ROUND_HALF_UP)."""

from decimal import Decimal

from app.utils.decimal_policy import (
    costo_promedio_ponderado,
    line_subtotal,
    money_round,
    qty_round,
)


def test_money_round_half_up() -> None:
    assert money_round(Decimal("1.225")) == Decimal("1.23")
    assert money_round(Decimal("1.224")) == Decimal("1.22")


def test_qty_round_half_up() -> None:
    assert qty_round(Decimal("1.23456")) == Decimal("1.2346")
    assert qty_round(Decimal("1.23454")) == Decimal("1.2345")


def test_line_subtotal() -> None:
    assert line_subtotal(Decimal("2.5"), Decimal("10.00")) == Decimal("25.00")


def test_costo_promedio_stock_cero() -> None:
    assert costo_promedio_ponderado(
        Decimal("0"), Decimal("0"), Decimal("100"), Decimal("12.50")
    ) == Decimal("12.50")


def test_costo_promedio_ponderado_basico() -> None:
    # (100*10 + 100*20) / 200 = 15
    assert costo_promedio_ponderado(
        Decimal("100"), Decimal("10"), Decimal("100"), Decimal("20")
    ) == Decimal("15.00")
