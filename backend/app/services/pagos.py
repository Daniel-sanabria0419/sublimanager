"""PagoService — anticipos/pagos de pedidos (§5.8, mínimo Stage 5).

saldo = total − Σ pagos CONFIRMADOS.
Al confirmar: genera exactamente un movimientos_caja ENTRADA.
No implementa gastos ni módulo de caja completo (Stage 7).
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictoNegocioError, RecursoNoEncontradoError, ValidacionError
from app.models.enums import EstadoPago, EstadoPedido, TipoCuentaCaja, TipoMovimientoCaja
from app.models.finanzas.cuentas_caja import CuentaCaja
from app.models.finanzas.metodos_pago import MetodoPago
from app.models.finanzas.movimientos_caja import MovimientoCaja
from app.models.finanzas.pagos import Pago
from app.models.pedidos.pedidos import Pedido
from app.repositories.finanzas import (
    CuentaCajaRepo,
    MetodoPagoRepo,
    MovimientoCajaRepo,
    PagoRepo,
)
from app.repositories.pedidos import PedidoRepo
from app.utils.decimal_policy import a_decimal, money_round


class MetodoPagoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = MetodoPagoRepo(db)

    def crear(self, *, nombre: str, activo: bool = True) -> MetodoPago:
        metodo = MetodoPago(nombre=nombre.strip(), activo=activo)
        try:
            self.repo.agregar(metodo)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictoNegocioError(
                f"Ya existe un método de pago '{nombre}'"
            ) from exc
        self.db.refresh(metodo)
        return metodo

    def listar(
        self, *, activo: bool | None = None, offset: int = 0, limit: int = 100
    ) -> list[MetodoPago]:
        return self.repo.listar(
            offset=offset, limit=limit, filtros={"activo": activo}
        )

    def obtener(self, id_: int) -> MetodoPago:
        return self.repo.obtener_o_404(id_, "metodo_pago")


class CuentaCajaService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CuentaCajaRepo(db)

    def crear(
        self, *, nombre: str, tipo_cuenta: str, activo: bool = True
    ) -> CuentaCaja:
        try:
            tipo = TipoCuentaCaja(tipo_cuenta).value
        except ValueError as exc:
            raise ValidacionError(
                f"tipo_cuenta inválido: {tipo_cuenta}"
            ) from exc
        cuenta = CuentaCaja(nombre=nombre.strip(), tipo_cuenta=tipo, activo=activo)
        try:
            self.repo.agregar(cuenta)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictoNegocioError(
                f"Ya existe una cuenta de caja '{nombre}'"
            ) from exc
        self.db.refresh(cuenta)
        return cuenta

    def listar(
        self, *, activo: bool | None = None, offset: int = 0, limit: int = 100
    ) -> list[CuentaCaja]:
        return self.repo.listar(
            offset=offset, limit=limit, filtros={"activo": activo}
        )

    def obtener(self, id_: int) -> CuentaCaja:
        return self.repo.obtener_o_404(id_, "cuenta_caja")


class PagoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.pagos = PagoRepo(db)
        self.pedidos = PedidoRepo(db)
        self.metodos = MetodoPagoRepo(db)
        self.cuentas = CuentaCajaRepo(db)
        self.movimientos = MovimientoCajaRepo(db)

    def obtener(self, id_: int) -> Pago:
        return self.pagos.obtener_o_404(id_, "pago")

    def listar_por_pedido(
        self,
        pedido_id: int,
        *,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Pago]:
        self.pedidos.obtener_o_404(pedido_id, "pedido")
        return self.pagos.listar_por_pedido(
            pedido_id, estado=estado, offset=offset, limit=limit
        )

    def saldo_pendiente(self, pedido_id: int) -> Decimal:
        pedido = self.pedidos.obtener_o_404(pedido_id, "pedido")
        pagado = money_round(self.pedidos.suma_pagos_confirmados(pedido_id))
        return money_round(money_round(pedido.total) - pagado)

    def registrar(
        self,
        *,
        pedido_id: int,
        metodo_pago_id: int,
        cuenta_caja_id: int,
        monto: Decimal | int | str,
        referencia: str | None = None,
        notas: str | None = None,
        confirmar: bool = True,
        fecha_pago: datetime | None = None,
    ) -> Pago:
        """Registra anticipo/pago. Si confirmar=True nace CONFIRMADO + caja."""
        # Bloqueo pesimista de la fila de pedido (§5.8).
        pedido = self.db.scalars(
            select(Pedido).where(Pedido.id == pedido_id).with_for_update()
        ).first()
        if pedido is None:
            raise RecursoNoEncontradoError(f"pedido id={pedido_id} no encontrado")
        if pedido.estado == EstadoPedido.CANCELADO:
            raise ConflictoNegocioError(
                "No se pueden registrar pagos en un pedido CANCELADO"
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
            money_round(pedido.total)
            - money_round(self.pedidos.suma_pagos_confirmados(pedido_id))
        )
        if confirmar and monto_m > saldo:
            raise ConflictoNegocioError(
                f"monto ({monto_m}) supera el saldo pendiente ({saldo})"
            )

        estado = (
            EstadoPago.CONFIRMADO if confirmar else EstadoPago.PENDIENTE
        )
        pago = Pago(
            pedido_id=pedido_id,
            metodo_pago_id=metodo_pago_id,
            cuenta_caja_id=cuenta_caja_id,
            monto=monto_m,
            fecha_pago=fecha_pago or datetime.now(timezone.utc),
            referencia=referencia,
            estado=estado,
            notas=notas,
        )
        self.pagos.agregar(pago)

        if confirmar:
            self._crear_movimiento_caja(pago)

        self.db.commit()
        self.db.refresh(pago)
        return pago

    def confirmar(self, id_: int, *, notas: str | None = None) -> Pago:
        pago = self.obtener(id_)
        if pago.estado != EstadoPago.PENDIENTE:
            raise ConflictoNegocioError(
                "Solo se pueden confirmar pagos en estado PENDIENTE"
            )

        pedido = self.db.scalars(
            select(Pedido).where(Pedido.id == pago.pedido_id).with_for_update()
        ).one()
        saldo = money_round(
            money_round(pedido.total)
            - money_round(self.pedidos.suma_pagos_confirmados(pedido.id))
        )
        if money_round(pago.monto) > saldo:
            raise ConflictoNegocioError(
                f"monto ({pago.monto}) supera el saldo pendiente ({saldo})"
            )

        pago.estado = EstadoPago.CONFIRMADO
        if notas is not None:
            pago.notas = notas
        self._crear_movimiento_caja(pago)
        self.db.commit()
        self.db.refresh(pago)
        return pago

    def anular(self, id_: int, *, notas: str | None = None) -> Pago:
        """Anula un pago PENDIENTE. CONFIRMADO no se anula en Stage 5 (Stage 7)."""
        pago = self.obtener(id_)
        if pago.estado != EstadoPago.PENDIENTE:
            raise ConflictoNegocioError(
                "Solo se pueden anular pagos en estado PENDIENTE en esta etapa"
            )
        pago.estado = EstadoPago.ANULADO
        if notas is not None:
            pago.notas = notas
        self.db.commit()
        self.db.refresh(pago)
        return pago

    def _crear_movimiento_caja(self, pago: Pago) -> MovimientoCaja:
        existente = self.movimientos.obtener_por_pago(pago.id)
        if existente is not None:
            raise ConflictoNegocioError(
                f"El pago id={pago.id} ya tiene movimiento de caja"
            )
        mov = MovimientoCaja(
            cuenta_caja_id=pago.cuenta_caja_id,
            tipo_movimiento=TipoMovimientoCaja.ENTRADA,
            monto=money_round(pago.monto),
            pago_id=pago.id,
            descripcion=f"Pago pedido id={pago.pedido_id}",
        )
        return self.movimientos.agregar(mov)
