"""PagoProveedorService — pagos parciales a proveedores ligados a compras (§5.9).

Al confirmar → movimientos_caja SALIDA con pago_proveedor_id (idempotente).
Las compras de inventario NO se contabilizan como gastos operativos.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictoNegocioError, RecursoNoEncontradoError, ValidacionError
from app.models.compras.compras import Compra
from app.models.enums import EstadoCompra, EstadoPago, TipoMovimientoCaja
from app.models.finanzas.movimientos_caja import MovimientoCaja
from app.models.finanzas.pagos_proveedor import PagoProveedor
from app.repositories.compras import CompraRepo
from app.repositories.finanzas import (
    CuentaCajaRepo,
    MetodoPagoRepo,
    MovimientoCajaRepo,
    PagoProveedorRepo,
)
from app.utils.decimal_policy import a_decimal, money_round


class PagoProveedorService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.pagos = PagoProveedorRepo(db)
        self.compras = CompraRepo(db)
        self.metodos = MetodoPagoRepo(db)
        self.cuentas = CuentaCajaRepo(db)
        self.movimientos = MovimientoCajaRepo(db)

    def obtener(self, id_: int) -> PagoProveedor:
        return self.pagos.obtener_o_404(id_, "pago_proveedor")

    def listar_por_compra(
        self,
        compra_id: int,
        *,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PagoProveedor]:
        self.compras.obtener_o_404(compra_id, "compra")
        return self.pagos.listar_por_compra(
            compra_id, estado=estado, offset=offset, limit=limit
        )

    def saldo_pendiente(self, compra_id: int) -> Decimal:
        compra = self.compras.obtener_o_404(compra_id, "compra")
        pagado = money_round(self.pagos.suma_confirmados_compra(compra_id))
        return money_round(money_round(compra.total) - pagado)

    def registrar(
        self,
        *,
        compra_id: int,
        metodo_pago_id: int,
        cuenta_caja_id: int,
        monto: Decimal | int | str,
        referencia: str | None = None,
        confirmar: bool = True,
        fecha_pago: datetime | None = None,
    ) -> PagoProveedor:
        compra = self.db.scalars(
            select(Compra).where(Compra.id == compra_id).with_for_update()
        ).first()
        if compra is None:
            raise RecursoNoEncontradoError(f"compra id={compra_id} no encontrado")
        if compra.estado == EstadoCompra.CANCELADA:
            raise ConflictoNegocioError(
                "No se pueden registrar pagos en una compra CANCELADA"
            )

        metodo = self.metodos.obtener_o_404(metodo_pago_id, "metodo_pago")
        if not metodo.activo:
            raise ValidacionError("El método de pago no está activo")
        cuenta = self.cuentas.obtener_o_404(cuenta_caja_id, "cuenta_caja")
        if not cuenta.activo:
            raise ValidacionError("La cuenta de caja no está activa")

        monto_m = money_round(a_decimal(monto))
        if monto_m <= 0:
            raise ValidacionError("monto debe ser > 0")

        saldo = money_round(
            money_round(compra.total)
            - money_round(self.pagos.suma_confirmados_compra(compra_id))
        )
        if confirmar and monto_m > saldo:
            raise ConflictoNegocioError(
                f"monto ({monto_m}) supera el saldo pendiente de la compra ({saldo})"
            )

        estado = EstadoPago.CONFIRMADO if confirmar else EstadoPago.PENDIENTE
        pago = PagoProveedor(
            compra_id=compra_id,
            metodo_pago_id=metodo_pago_id,
            cuenta_caja_id=cuenta_caja_id,
            monto=monto_m,
            fecha_pago=fecha_pago or datetime.now(timezone.utc),
            estado=estado,
            referencia=referencia,
        )
        self.pagos.agregar(pago)

        if confirmar:
            self._crear_movimiento_caja(pago)

        self.db.commit()
        self.db.refresh(pago)
        return pago

    def confirmar(self, id_: int) -> PagoProveedor:
        pago = self.obtener(id_)
        if pago.estado == EstadoPago.CONFIRMADO:
            self._crear_movimiento_caja(pago, idempotente=True)
            self.db.commit()
            self.db.refresh(pago)
            return pago
        if pago.estado == EstadoPago.ANULADO:
            raise ConflictoNegocioError("No se puede confirmar un pago ANULADO")
        if pago.estado != EstadoPago.PENDIENTE:
            raise ConflictoNegocioError(
                f"Estado de pago no confirmable: {pago.estado}"
            )

        compra = self.db.scalars(
            select(Compra).where(Compra.id == pago.compra_id).with_for_update()
        ).one()
        saldo = money_round(
            money_round(compra.total)
            - money_round(self.pagos.suma_confirmados_compra(compra.id))
        )
        if money_round(pago.monto) > saldo:
            raise ConflictoNegocioError(
                f"monto ({pago.monto}) supera el saldo pendiente de la compra ({saldo})"
            )

        pago.estado = EstadoPago.CONFIRMADO
        self._crear_movimiento_caja(pago, idempotente=True)
        self.db.commit()
        self.db.refresh(pago)
        return pago

    def anular(self, id_: int) -> PagoProveedor:
        pago = self.obtener(id_)
        if pago.estado == EstadoPago.ANULADO:
            return pago

        if pago.estado == EstadoPago.CONFIRMADO:
            mov = self.movimientos.obtener_por_pago_proveedor(pago.id)
            if mov is not None:
                self.movimientos.eliminar(mov)

        pago.estado = EstadoPago.ANULADO
        self.db.commit()
        self.db.refresh(pago)
        return pago

    def _crear_movimiento_caja(
        self, pago: PagoProveedor, *, idempotente: bool = False
    ) -> MovimientoCaja:
        existente = self.movimientos.obtener_por_pago_proveedor(pago.id)
        if existente is not None:
            if idempotente:
                return existente
            raise ConflictoNegocioError(
                f"El pago_proveedor id={pago.id} ya tiene movimiento de caja"
            )
        mov = MovimientoCaja(
            cuenta_caja_id=pago.cuenta_caja_id,
            tipo_movimiento=TipoMovimientoCaja.SALIDA,
            monto=money_round(pago.monto),
            pago_proveedor_id=pago.id,
            descripcion=f"Pago proveedor compra id={pago.compra_id}",
        )
        try:
            with self.db.begin_nested():
                return self.movimientos.agregar(mov)
        except IntegrityError as exc:
            if idempotente:
                existente2 = self.movimientos.obtener_por_pago_proveedor(pago.id)
                if existente2 is not None:
                    return existente2
            raise ConflictoNegocioError(
                f"El pago_proveedor id={pago.id} ya tiene movimiento de caja"
            ) from exc
