"""Repositorios mínimos de finanzas para anticipos de pedidos (Stage 5)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.finanzas.cuentas_caja import CuentaCaja
from app.models.finanzas.metodos_pago import MetodoPago
from app.models.finanzas.movimientos_caja import MovimientoCaja
from app.models.finanzas.pagos import Pago
from app.repositories.base import RepositorioBase


class MetodoPagoRepo(RepositorioBase[MetodoPago]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, MetodoPago)

    def obtener_por_nombre(self, nombre: str) -> MetodoPago | None:
        stmt = select(MetodoPago).where(MetodoPago.nombre == nombre)
        return self.db.scalars(stmt).first()


class CuentaCajaRepo(RepositorioBase[CuentaCaja]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, CuentaCaja)

    def obtener_por_nombre(self, nombre: str) -> CuentaCaja | None:
        stmt = select(CuentaCaja).where(CuentaCaja.nombre == nombre)
        return self.db.scalars(stmt).first()


class PagoRepo(RepositorioBase[Pago]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Pago)

    def listar_por_pedido(
        self,
        pedido_id: int,
        *,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Pago]:
        stmt = select(Pago).where(Pago.pedido_id == pedido_id)
        if estado is not None:
            stmt = stmt.where(Pago.estado == estado)
        stmt = stmt.offset(offset).limit(limit).order_by(Pago.id)
        return list(self.db.scalars(stmt).all())


class MovimientoCajaRepo(RepositorioBase[MovimientoCaja]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, MovimientoCaja)

    def obtener_por_pago(self, pago_id: int) -> MovimientoCaja | None:
        stmt = select(MovimientoCaja).where(MovimientoCaja.pago_id == pago_id)
        return self.db.scalars(stmt).first()
