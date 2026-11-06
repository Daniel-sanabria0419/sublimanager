"""GastoService / PagoGastoService — gastos operativos y pagos parciales (§5.9).

Compras de inventario NO son gastos (van por compras + pagos_proveedor).
Al confirmar pago_gasto → movimientos_caja SALIDA (idempotente, un origen).
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictoNegocioError, RecursoNoEncontradoError, ValidacionError
from app.models.enums import EstadoPago, EstadoPagoGasto, TipoMovimientoCaja
from app.models.finanzas.categorias_gasto import CategoriaGasto
from app.models.finanzas.gastos import Gasto
from app.models.finanzas.movimientos_caja import MovimientoCaja
from app.models.finanzas.pagos_gasto import PagoGasto
from app.repositories.finanzas import (
    CategoriaGastoRepo,
    CuentaCajaRepo,
    GastoRepo,
    MetodoPagoRepo,
    MovimientoCajaRepo,
    PagoGastoRepo,
)
from app.utils.decimal_policy import a_decimal, money_round


class CategoriaGastoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CategoriaGastoRepo(db)

    def crear(
        self,
        *,
        nombre: str,
        descripcion: str | None = None,
        activo: bool = True,
    ) -> CategoriaGasto:
        cat = CategoriaGasto(
            nombre=nombre.strip(),
            descripcion=descripcion,
            activo=activo,
        )
        try:
            self.repo.agregar(cat)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictoNegocioError(
                f"Ya existe la categoría de gasto '{nombre}'"
            ) from exc
        self.db.refresh(cat)
        return cat

    def listar(
        self, *, activo: bool | None = None, offset: int = 0, limit: int = 100
    ) -> list[CategoriaGasto]:
        return self.repo.listar(
            offset=offset, limit=limit, filtros={"activo": activo}
        )

    def obtener(self, id_: int) -> CategoriaGasto:
        return self.repo.obtener_o_404(id_, "categoria_gasto")

    def actualizar(
        self,
        id_: int,
        *,
        nombre: str | None = None,
        descripcion: str | None = None,
        activo: bool | None = None,
    ) -> CategoriaGasto:
        cat = self.obtener(id_)
        if nombre is not None:
            cat.nombre = nombre.strip()
        if descripcion is not None:
            cat.descripcion = descripcion
        if activo is not None:
            cat.activo = activo
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictoNegocioError(
                "Nombre de categoría de gasto duplicado"
            ) from exc
        self.db.refresh(cat)
        return cat

    def eliminar(self, id_: int) -> None:
        cat = self.obtener(id_)
        cat.activo = False
        self.db.commit()


class GastoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.gastos = GastoRepo(db)
        self.categorias = CategoriaGastoRepo(db)
        self.pagos = PagoGastoRepo(db)

    def obtener(self, id_: int) -> Gasto:
        return self.gastos.obtener_o_404(id_, "gasto")

    def listar(
        self,
        *,
        categoria_id: int | None = None,
        estado_pago: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Gasto]:
        return self.gastos.listar_filtrado(
            categoria_id=categoria_id,
            estado_pago=estado_pago,
            offset=offset,
            limit=limit,
        )

    def saldo_pendiente(self, gasto_id: int) -> Decimal:
        gasto = self.obtener(gasto_id)
        pagado = money_round(self.gastos.suma_pagos_confirmados(gasto_id))
        return money_round(money_round(gasto.monto) - pagado)

    def detalle_saldos(self, gasto: Gasto) -> tuple[Decimal, Decimal]:
        pagado = money_round(self.gastos.suma_pagos_confirmados(gasto.id))
        saldo = money_round(money_round(gasto.monto) - pagado)
        return pagado, saldo

    def crear(
        self,
        *,
        categoria_id: int,
        descripcion: str,
        monto: Decimal | int | str,
        fecha_gasto: datetime | None = None,
        notas: str | None = None,
    ) -> Gasto:
        cat = self.categorias.obtener_o_404(categoria_id, "categoria_gasto")
        if not cat.activo:
            raise ValidacionError("La categoría de gasto no está activa")
        monto_m = money_round(a_decimal(monto))
        if monto_m <= 0:
            raise ValidacionError("monto debe ser > 0")
        gasto = Gasto(
            categoria_id=categoria_id,
            descripcion=descripcion.strip(),
            monto=monto_m,
            fecha_gasto=fecha_gasto or datetime.now(timezone.utc),
            estado_pago=EstadoPagoGasto.NO_PAGADO,
            notas=notas,
        )
        self.gastos.agregar(gasto)
        self.db.commit()
        self.db.refresh(gasto)
        return gasto

    def actualizar(
        self,
        id_: int,
        *,
        categoria_id: int | None = None,
        descripcion: str | None = None,
        notas: str | None = None,
    ) -> Gasto:
        gasto = self.obtener(id_)
        if gasto.estado_pago == EstadoPagoGasto.ANULADO:
            raise ConflictoNegocioError("No se puede editar un gasto ANULADO")
        if categoria_id is not None:
            cat = self.categorias.obtener_o_404(categoria_id, "categoria_gasto")
            if not cat.activo:
                raise ValidacionError("La categoría de gasto no está activa")
            gasto.categoria_id = categoria_id
        if descripcion is not None:
            gasto.descripcion = descripcion.strip()
        if notas is not None:
            gasto.notas = notas
        self.db.commit()
        self.db.refresh(gasto)
        return gasto

    def anular(self, id_: int, *, notas: str | None = None) -> Gasto:
        gasto = self.obtener(id_)
        if gasto.estado_pago == EstadoPagoGasto.ANULADO:
            return gasto
        # Solo anular si no hay pagos CONFIRMADOS
        pagado = money_round(self.gastos.suma_pagos_confirmados(id_))
        if pagado > 0:
            raise ConflictoNegocioError(
                "No se puede anular un gasto con pagos CONFIRMADOS; "
                "anule primero los pagos"
            )
        gasto.estado_pago = EstadoPagoGasto.ANULADO
        if notas is not None:
            gasto.notas = notas
        self.db.commit()
        self.db.refresh(gasto)
        return gasto

    def _recalcular_estado_pago(self, gasto: Gasto) -> None:
        pagado = money_round(self.gastos.suma_pagos_confirmados(gasto.id))
        total = money_round(gasto.monto)
        if pagado <= 0:
            gasto.estado_pago = EstadoPagoGasto.NO_PAGADO
        elif pagado >= total:
            gasto.estado_pago = EstadoPagoGasto.PAGADO
        else:
            gasto.estado_pago = EstadoPagoGasto.PARCIAL


class PagoGastoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.pagos = PagoGastoRepo(db)
        self.gastos = GastoRepo(db)
        self.metodos = MetodoPagoRepo(db)
        self.cuentas = CuentaCajaRepo(db)
        self.movimientos = MovimientoCajaRepo(db)
        self.gasto_svc = GastoService(db)

    def obtener(self, id_: int) -> PagoGasto:
        return self.pagos.obtener_o_404(id_, "pago_gasto")

    def listar_por_gasto(
        self,
        gasto_id: int,
        *,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PagoGasto]:
        self.gastos.obtener_o_404(gasto_id, "gasto")
        return self.pagos.listar_por_gasto(
            gasto_id, estado=estado, offset=offset, limit=limit
        )

    def registrar(
        self,
        *,
        gasto_id: int,
        metodo_pago_id: int,
        cuenta_caja_id: int,
        monto: Decimal | int | str,
        referencia: str | None = None,
        confirmar: bool = True,
        fecha_pago: datetime | None = None,
    ) -> PagoGasto:
        gasto = self.db.scalars(
            select(Gasto).where(Gasto.id == gasto_id).with_for_update()
        ).first()
        if gasto is None:
            raise RecursoNoEncontradoError(f"gasto id={gasto_id} no encontrado")
        if gasto.estado_pago == EstadoPagoGasto.ANULADO:
            raise ConflictoNegocioError(
                "No se pueden registrar pagos en un gasto ANULADO"
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
            money_round(gasto.monto)
            - money_round(self.gastos.suma_pagos_confirmados(gasto_id))
        )
        if confirmar and monto_m > saldo:
            raise ConflictoNegocioError(
                f"monto ({monto_m}) supera el saldo pendiente del gasto ({saldo})"
            )

        estado = EstadoPago.CONFIRMADO if confirmar else EstadoPago.PENDIENTE
        pago = PagoGasto(
            gasto_id=gasto_id,
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
            self.gasto_svc._recalcular_estado_pago(gasto)

        self.db.commit()
        self.db.refresh(pago)
        return pago

    def confirmar(self, id_: int) -> PagoGasto:
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

        gasto = self.db.scalars(
            select(Gasto).where(Gasto.id == pago.gasto_id).with_for_update()
        ).one()
        saldo = money_round(
            money_round(gasto.monto)
            - money_round(self.gastos.suma_pagos_confirmados(gasto.id))
        )
        if money_round(pago.monto) > saldo:
            raise ConflictoNegocioError(
                f"monto ({pago.monto}) supera el saldo pendiente del gasto ({saldo})"
            )

        pago.estado = EstadoPago.CONFIRMADO
        self._crear_movimiento_caja(pago, idempotente=True)
        self.gasto_svc._recalcular_estado_pago(gasto)
        self.db.commit()
        self.db.refresh(pago)
        return pago

    def anular(self, id_: int) -> PagoGasto:
        pago = self.obtener(id_)
        if pago.estado == EstadoPago.ANULADO:
            return pago

        gasto = self.db.scalars(
            select(Gasto).where(Gasto.id == pago.gasto_id).with_for_update()
        ).one()

        if pago.estado == EstadoPago.CONFIRMADO:
            mov = self.movimientos.obtener_por_pago_gasto(pago.id)
            if mov is not None:
                self.movimientos.eliminar(mov)

        pago.estado = EstadoPago.ANULADO
        self.db.flush()
        if gasto.estado_pago != EstadoPagoGasto.ANULADO:
            self.gasto_svc._recalcular_estado_pago(gasto)
        self.db.commit()
        self.db.refresh(pago)
        return pago

    def _crear_movimiento_caja(
        self, pago: PagoGasto, *, idempotente: bool = False
    ) -> MovimientoCaja:
        existente = self.movimientos.obtener_por_pago_gasto(pago.id)
        if existente is not None:
            if idempotente:
                return existente
            raise ConflictoNegocioError(
                f"El pago_gasto id={pago.id} ya tiene movimiento de caja"
            )
        mov = MovimientoCaja(
            cuenta_caja_id=pago.cuenta_caja_id,
            tipo_movimiento=TipoMovimientoCaja.SALIDA,
            monto=money_round(pago.monto),
            pago_gasto_id=pago.id,
            descripcion=f"Pago gasto id={pago.gasto_id}",
        )
        try:
            with self.db.begin_nested():
                return self.movimientos.agregar(mov)
        except IntegrityError as exc:
            if idempotente:
                existente2 = self.movimientos.obtener_por_pago_gasto(pago.id)
                if existente2 is not None:
                    return existente2
            raise ConflictoNegocioError(
                f"El pago_gasto id={pago.id} ya tiene movimiento de caja"
            ) from exc
