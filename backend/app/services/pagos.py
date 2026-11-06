"""PagoService — anticipos/pagos de pedidos (§5.8) + catálogos de pago/caja.

Stage 7: CRUD completo de métodos/cuentas; anulación de CONFIRMADO
(elimina movimiento_caja asociado); confirmación idempotente.
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

    def actualizar(
        self,
        id_: int,
        *,
        nombre: str | None = None,
        activo: bool | None = None,
    ) -> MetodoPago:
        metodo = self.obtener(id_)
        if nombre is not None:
            metodo.nombre = nombre.strip()
        if activo is not None:
            metodo.activo = activo
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictoNegocioError("Nombre de método de pago duplicado") from exc
        self.db.refresh(metodo)
        return metodo

    def eliminar(self, id_: int) -> None:
        """Baja lógica (activo=false) — no borra filas referenciadas."""
        metodo = self.obtener(id_)
        metodo.activo = False
        self.db.commit()


class CuentaCajaService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CuentaCajaRepo(db)
        self.movimientos = MovimientoCajaRepo(db)

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

    def actualizar(
        self,
        id_: int,
        *,
        nombre: str | None = None,
        tipo_cuenta: str | None = None,
        activo: bool | None = None,
    ) -> CuentaCaja:
        cuenta = self.obtener(id_)
        if nombre is not None:
            cuenta.nombre = nombre.strip()
        if tipo_cuenta is not None:
            try:
                cuenta.tipo_cuenta = TipoCuentaCaja(tipo_cuenta).value
            except ValueError as exc:
                raise ValidacionError(
                    f"tipo_cuenta inválido: {tipo_cuenta}"
                ) from exc
        if activo is not None:
            cuenta.activo = activo
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictoNegocioError("Nombre de cuenta de caja duplicado") from exc
        self.db.refresh(cuenta)
        return cuenta

    def eliminar(self, id_: int) -> None:
        cuenta = self.obtener(id_)
        cuenta.activo = False
        self.db.commit()

    def saldo(self, id_: int) -> Decimal:
        self.obtener(id_)
        return money_round(self.movimientos.saldo_cuenta(id_))


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
        """Confirma pago PENDIENTE. Idempotente si ya está CONFIRMADO (§ Stage 7)."""
        pago = self.obtener(id_)

        if pago.estado == EstadoPago.CONFIRMADO:
            # Idempotencia: asegura un único movimiento_caja.
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
        self._crear_movimiento_caja(pago, idempotente=True)
        self.db.commit()
        self.db.refresh(pago)
        return pago

    def anular(self, id_: int, *, notas: str | None = None) -> Pago:
        """Anula PENDIENTE o CONFIRMADO. Si había caja, elimina el movimiento."""
        pago = self.obtener(id_)
        if pago.estado == EstadoPago.ANULADO:
            return pago

        if pago.estado == EstadoPago.CONFIRMADO:
            mov = self.movimientos.obtener_por_pago(pago.id)
            if mov is not None:
                self.movimientos.eliminar(mov)

        pago.estado = EstadoPago.ANULADO
        if notas is not None:
            pago.notas = notas
        self.db.commit()
        self.db.refresh(pago)
        return pago

    def _crear_movimiento_caja(
        self, pago: Pago, *, idempotente: bool = False
    ) -> MovimientoCaja:
        existente = self.movimientos.obtener_por_pago(pago.id)
        if existente is not None:
            if idempotente:
                return existente
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
        try:
            with self.db.begin_nested():
                return self.movimientos.agregar(mov)
        except IntegrityError as exc:
            if idempotente:
                existente2 = self.movimientos.obtener_por_pago(pago.id)
                if existente2 is not None:
                    return existente2
            raise ConflictoNegocioError(
                f"El pago id={pago.id} ya tiene movimiento de caja"
            ) from exc
