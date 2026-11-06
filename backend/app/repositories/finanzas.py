"""Repositorios del módulo Finanzas (Stage 5 mínimo + Stage 7 completo)."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import EstadoPago, EstadoPagoGasto, EstadoPedido, TipoMovimientoCaja
from app.models.finanzas.categorias_gasto import CategoriaGasto
from app.models.finanzas.cuentas_caja import CuentaCaja
from app.models.finanzas.gastos import Gasto
from app.models.finanzas.metodos_pago import MetodoPago
from app.models.finanzas.movimientos_caja import MovimientoCaja
from app.models.finanzas.pagos import Pago
from app.models.finanzas.pagos_gasto import PagoGasto
from app.models.finanzas.pagos_proveedor import PagoProveedor
from app.models.pedidos.pedidos import Pedido
from app.models.compras.compras import Compra
from app.models.produccion.asientos_costo_produccion import AsientoCostoProduccion
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

    def suma_confirmados_pedido(self, pedido_id: int) -> Decimal:
        stmt = select(func.coalesce(func.sum(Pago.monto), 0)).where(
            Pago.pedido_id == pedido_id,
            Pago.estado == EstadoPago.CONFIRMADO,
        )
        return Decimal(str(self.db.scalar(stmt) or 0))


class MovimientoCajaRepo(RepositorioBase[MovimientoCaja]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, MovimientoCaja)

    def obtener_por_pago(self, pago_id: int) -> MovimientoCaja | None:
        stmt = select(MovimientoCaja).where(MovimientoCaja.pago_id == pago_id)
        return self.db.scalars(stmt).first()

    def obtener_por_pago_gasto(self, pago_gasto_id: int) -> MovimientoCaja | None:
        stmt = select(MovimientoCaja).where(
            MovimientoCaja.pago_gasto_id == pago_gasto_id
        )
        return self.db.scalars(stmt).first()

    def obtener_por_pago_proveedor(
        self, pago_proveedor_id: int
    ) -> MovimientoCaja | None:
        stmt = select(MovimientoCaja).where(
            MovimientoCaja.pago_proveedor_id == pago_proveedor_id
        )
        return self.db.scalars(stmt).first()

    def listar_filtrado(
        self,
        *,
        cuenta_caja_id: int | None = None,
        tipo_movimiento: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[MovimientoCaja]:
        stmt = select(MovimientoCaja)
        if cuenta_caja_id is not None:
            stmt = stmt.where(MovimientoCaja.cuenta_caja_id == cuenta_caja_id)
        if tipo_movimiento is not None:
            stmt = stmt.where(MovimientoCaja.tipo_movimiento == tipo_movimiento)
        stmt = stmt.offset(offset).limit(limit).order_by(MovimientoCaja.id)
        return list(self.db.scalars(stmt).all())

    def saldo_cuenta(self, cuenta_caja_id: int) -> Decimal:
        entradas = self.db.scalar(
            select(func.coalesce(func.sum(MovimientoCaja.monto), 0)).where(
                MovimientoCaja.cuenta_caja_id == cuenta_caja_id,
                MovimientoCaja.tipo_movimiento == TipoMovimientoCaja.ENTRADA,
            )
        )
        salidas = self.db.scalar(
            select(func.coalesce(func.sum(MovimientoCaja.monto), 0)).where(
                MovimientoCaja.cuenta_caja_id == cuenta_caja_id,
                MovimientoCaja.tipo_movimiento == TipoMovimientoCaja.SALIDA,
            )
        )
        return Decimal(str(entradas or 0)) - Decimal(str(salidas or 0))

    def totales_movimientos(self) -> tuple[Decimal, Decimal]:
        entradas = self.db.scalar(
            select(func.coalesce(func.sum(MovimientoCaja.monto), 0)).where(
                MovimientoCaja.tipo_movimiento == TipoMovimientoCaja.ENTRADA
            )
        )
        salidas = self.db.scalar(
            select(func.coalesce(func.sum(MovimientoCaja.monto), 0)).where(
                MovimientoCaja.tipo_movimiento == TipoMovimientoCaja.SALIDA
            )
        )
        return Decimal(str(entradas or 0)), Decimal(str(salidas or 0))


class CategoriaGastoRepo(RepositorioBase[CategoriaGasto]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, CategoriaGasto)

    def obtener_por_nombre(self, nombre: str) -> CategoriaGasto | None:
        stmt = select(CategoriaGasto).where(CategoriaGasto.nombre == nombre)
        return self.db.scalars(stmt).first()


class GastoRepo(RepositorioBase[Gasto]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Gasto)

    def obtener_con_pagos(self, id_: int) -> Gasto | None:
        stmt = (
            select(Gasto)
            .where(Gasto.id == id_)
            .options(selectinload(Gasto.pagos))
        )
        return self.db.scalars(stmt).first()

    def listar_filtrado(
        self,
        *,
        categoria_id: int | None = None,
        estado_pago: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Gasto]:
        stmt = select(Gasto)
        if categoria_id is not None:
            stmt = stmt.where(Gasto.categoria_id == categoria_id)
        if estado_pago is not None:
            stmt = stmt.where(Gasto.estado_pago == estado_pago)
        stmt = stmt.offset(offset).limit(limit).order_by(Gasto.id)
        return list(self.db.scalars(stmt).all())

    def suma_pagos_confirmados(self, gasto_id: int) -> Decimal:
        stmt = select(func.coalesce(func.sum(PagoGasto.monto), 0)).where(
            PagoGasto.gasto_id == gasto_id,
            PagoGasto.estado == EstadoPago.CONFIRMADO,
        )
        return Decimal(str(self.db.scalar(stmt) or 0))

    def ids_vinculados_produccion(self) -> set[int]:
        """Gastos ya asignados a asientos de costo (evitar doble conteo §5.9)."""
        stmt = select(AsientoCostoProduccion.gasto_id).where(
            AsientoCostoProduccion.gasto_id.is_not(None)
        )
        return {int(g) for g in self.db.scalars(stmt).all() if g is not None}

    def suma_gastos_operativos_sin_produccion(self) -> Decimal:
        """Suma montos de gastos no ANULADOS excluyendo los ligados a OP."""
        vinculados = self.ids_vinculados_produccion()
        stmt = select(Gasto).where(Gasto.estado_pago != EstadoPagoGasto.ANULADO)
        total = Decimal("0")
        for gasto in self.db.scalars(stmt).all():
            if gasto.id in vinculados:
                continue
            total += Decimal(str(gasto.monto))
        return total


class PagoGastoRepo(RepositorioBase[PagoGasto]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, PagoGasto)

    def listar_por_gasto(
        self,
        gasto_id: int,
        *,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PagoGasto]:
        stmt = select(PagoGasto).where(PagoGasto.gasto_id == gasto_id)
        if estado is not None:
            stmt = stmt.where(PagoGasto.estado == estado)
        stmt = stmt.offset(offset).limit(limit).order_by(PagoGasto.id)
        return list(self.db.scalars(stmt).all())


class PagoProveedorRepo(RepositorioBase[PagoProveedor]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, PagoProveedor)

    def listar_por_compra(
        self,
        compra_id: int,
        *,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PagoProveedor]:
        stmt = select(PagoProveedor).where(PagoProveedor.compra_id == compra_id)
        if estado is not None:
            stmt = stmt.where(PagoProveedor.estado == estado)
        stmt = stmt.offset(offset).limit(limit).order_by(PagoProveedor.id)
        return list(self.db.scalars(stmt).all())

    def suma_confirmados_compra(self, compra_id: int) -> Decimal:
        stmt = select(func.coalesce(func.sum(PagoProveedor.monto), 0)).where(
            PagoProveedor.compra_id == compra_id,
            PagoProveedor.estado == EstadoPago.CONFIRMADO,
        )
        return Decimal(str(self.db.scalar(stmt) or 0))


class ConsultasFinancierasRepo:
    """Consultas de CxC / CxP / resumen (§5.10) — solo lectura."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def cuentas_por_cobrar(self) -> list[dict]:
        """Pedidos no CANCELADOS con saldo > 0 (total − CONFIRMADOS)."""
        pedidos = list(
            self.db.scalars(
                select(Pedido).where(Pedido.estado != EstadoPedido.CANCELADO).order_by(
                    Pedido.id
                )
            ).all()
        )
        filas: list[dict] = []
        for pedido in pedidos:
            pagado = Decimal(
                str(
                    self.db.scalar(
                        select(func.coalesce(func.sum(Pago.monto), 0)).where(
                            Pago.pedido_id == pedido.id,
                            Pago.estado == EstadoPago.CONFIRMADO,
                        )
                    )
                    or 0
                )
            )
            total = Decimal(str(pedido.total))
            saldo = total - pagado
            if saldo <= 0:
                continue
            filas.append(
                {
                    "pedido_id": pedido.id,
                    "numero_pedido": pedido.numero_pedido,
                    "cliente_id": pedido.cliente_id,
                    "estado": pedido.estado,
                    "total": total,
                    "total_pagado": pagado,
                    "saldo_pendiente": saldo,
                }
            )
        return filas

    def cuentas_por_pagar(self) -> list[dict]:
        """Compras no CANCELADAS con saldo proveedor > 0."""
        compras = list(
            self.db.scalars(
                select(Compra)
                .where(Compra.estado != "CANCELADA")
                .order_by(Compra.id)
            ).all()
        )
        filas: list[dict] = []
        for compra in compras:
            pagado = Decimal(
                str(
                    self.db.scalar(
                        select(func.coalesce(func.sum(PagoProveedor.monto), 0)).where(
                            PagoProveedor.compra_id == compra.id,
                            PagoProveedor.estado == EstadoPago.CONFIRMADO,
                        )
                    )
                    or 0
                )
            )
            total = Decimal(str(compra.total))
            saldo = total - pagado
            if saldo <= 0:
                continue
            filas.append(
                {
                    "compra_id": compra.id,
                    "proveedor_id": compra.proveedor_id,
                    "numero_factura": compra.numero_factura,
                    "estado": compra.estado,
                    "total": total,
                    "total_pagado": pagado,
                    "saldo_pendiente": saldo,
                }
            )
        return filas

    def ventas_reconocidas(self) -> Decimal:
        """Ventas = pedidos ENTREGADOS (§5.10)."""
        valor = self.db.scalar(
            select(func.coalesce(func.sum(Pedido.total), 0)).where(
                Pedido.estado == EstadoPedido.ENTREGADO
            )
        )
        return Decimal(str(valor or 0))

    def dinero_recibido_clientes(self) -> Decimal:
        """Cobros CONFIRMADOS de pedidos (caja ENTRADA por pagos)."""
        valor = self.db.scalar(
            select(func.coalesce(func.sum(Pago.monto), 0)).where(
                Pago.estado == EstadoPago.CONFIRMADO
            )
        )
        return Decimal(str(valor or 0))

    def total_cxc(self) -> Decimal:
        return sum(
            (f["saldo_pendiente"] for f in self.cuentas_por_cobrar()),
            Decimal("0"),
        )

    def total_cxp(self) -> Decimal:
        return sum(
            (f["saldo_pendiente"] for f in self.cuentas_por_pagar()),
            Decimal("0"),
        )

    def costos_produccion_reales(self) -> Decimal:
        """Costos de fabricación REAL (asientos); no incluye compras de inventario."""
        from app.models.enums import EtapaCosto

        valor = self.db.scalar(
            select(func.coalesce(func.sum(AsientoCostoProduccion.costo_total), 0)).where(
                AsientoCostoProduccion.etapa_costo == EtapaCosto.REAL
            )
        )
        return Decimal(str(valor or 0))
