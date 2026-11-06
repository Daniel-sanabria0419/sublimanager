"""Repositorio de consultas de reportes (Stage 9) — solo lectura."""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from decimal import Decimal

from sqlalchemy import Date, case, cast, extract, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.compras.compras import Compra
from app.models.enums import EstadoPago, EstadoPagoGasto, EstadoPedido, EtapaCosto
from app.models.finanzas.categorias_gasto import CategoriaGasto
from app.models.finanzas.gastos import Gasto
from app.models.finanzas.pagos import Pago
from app.models.inventario.bodegas import Bodega
from app.models.inventario.existencias import Existencia
from app.models.inventario.materiales import Material
from app.models.pedidos.items_pedido import ItemPedido
from app.models.pedidos.pedidos import Pedido
from app.models.produccion.asientos_costo_produccion import AsientoCostoProduccion
from app.models.produccion.consumos_produccion import ConsumoProduccion
from app.models.productos.productos import Producto
from app.models.productos.variantes_producto import VarianteProducto
from app.models.recetas.categorias_costo import CategoriaCosto
from app.repositories.finanzas import ConsultasFinancierasRepo, GastoRepo


def _inicio_dia(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=timezone.utc)


def _fin_dia(d: date) -> datetime:
    return datetime.combine(d, time.max, tzinfo=timezone.utc)


class ReportesRepo:
    """Agregaciones de reportes sobre datos reales (§5.10 / Stage 9)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.finanzas = ConsultasFinancierasRepo(db)
        self.gastos_repo = GastoRepo(db)

    # ------------------------------------------------------------------
    # Ventas
    # ------------------------------------------------------------------

    def ventas_diarias(
        self,
        *,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[dict]:
        """Ventas reconocidas (pedidos ENTREGADOS) agrupadas por día."""
        stmt = (
            select(
                cast(Pedido.fecha_pedido, Date).label("fecha"),
                func.count(Pedido.id).label("cantidad_pedidos"),
                func.coalesce(func.sum(Pedido.total), 0).label("total_ventas"),
            )
            .where(Pedido.estado == EstadoPedido.ENTREGADO)
            .group_by(cast(Pedido.fecha_pedido, Date))
            .order_by(cast(Pedido.fecha_pedido, Date))
        )
        if fecha_desde is not None:
            stmt = stmt.where(Pedido.fecha_pedido >= _inicio_dia(fecha_desde))
        if fecha_hasta is not None:
            stmt = stmt.where(Pedido.fecha_pedido <= _fin_dia(fecha_hasta))
        filas = []
        for row in self.db.execute(stmt).all():
            filas.append(
                {
                    "fecha": row.fecha.isoformat() if row.fecha else None,
                    "cantidad_pedidos": int(row.cantidad_pedidos or 0),
                    "total_ventas": Decimal(str(row.total_ventas or 0)),
                }
            )
        return filas

    def ventas_mensuales(
        self,
        *,
        anio: int | None = None,
    ) -> list[dict]:
        """Ventas reconocidas agrupadas por año-mes."""
        anio_col = extract("year", Pedido.fecha_pedido)
        mes_col = extract("month", Pedido.fecha_pedido)
        stmt = (
            select(
                anio_col.label("anio"),
                mes_col.label("mes"),
                func.count(Pedido.id).label("cantidad_pedidos"),
                func.coalesce(func.sum(Pedido.total), 0).label("total_ventas"),
            )
            .where(Pedido.estado == EstadoPedido.ENTREGADO)
            .group_by(anio_col, mes_col)
            .order_by(anio_col, mes_col)
        )
        if anio is not None:
            stmt = stmt.where(anio_col == anio)
        filas = []
        for row in self.db.execute(stmt).all():
            a = int(row.anio)
            m = int(row.mes)
            filas.append(
                {
                    "anio": a,
                    "mes": m,
                    "periodo": f"{a:04d}-{m:02d}",
                    "cantidad_pedidos": int(row.cantidad_pedidos or 0),
                    "total_ventas": Decimal(str(row.total_ventas or 0)),
                }
            )
        return filas

    def productos_mas_vendidos(
        self,
        *,
        limite: int = 20,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[dict]:
        """Top productos por cantidad en pedidos ENTREGADOS."""
        stmt = (
            select(
                Producto.id.label("producto_id"),
                Producto.nombre.label("nombre"),
                Producto.tipo_producto.label("tipo_producto"),
                func.coalesce(func.sum(ItemPedido.cantidad), 0).label("cantidad_vendida"),
                func.coalesce(func.sum(ItemPedido.subtotal), 0).label("total_ventas"),
            )
            .join(ItemPedido, ItemPedido.producto_id == Producto.id)
            .join(Pedido, Pedido.id == ItemPedido.pedido_id)
            .where(Pedido.estado == EstadoPedido.ENTREGADO)
            .group_by(Producto.id, Producto.nombre, Producto.tipo_producto)
            .order_by(func.sum(ItemPedido.cantidad).desc())
            .limit(limite)
        )
        if fecha_desde is not None:
            stmt = stmt.where(Pedido.fecha_pedido >= _inicio_dia(fecha_desde))
        if fecha_hasta is not None:
            stmt = stmt.where(Pedido.fecha_pedido <= _fin_dia(fecha_hasta))
        return [
            {
                "producto_id": int(row.producto_id),
                "nombre": row.nombre,
                "tipo_producto": row.tipo_producto,
                "cantidad_vendida": Decimal(str(row.cantidad_vendida or 0)),
                "total_ventas": Decimal(str(row.total_ventas or 0)),
            }
            for row in self.db.execute(stmt).all()
        ]

    def utilidad_por_producto(
        self,
        *,
        limite: int = 50,
    ) -> list[dict]:
        """Utilidad estimada por producto en pedidos ENTREGADOS.

        utilidad = Σ (precio_venta_unitario − costo_unitario_estimado) × cantidad
        """
        ingreso = func.coalesce(func.sum(ItemPedido.subtotal), 0)
        costo = func.coalesce(
            func.sum(ItemPedido.costo_unitario_estimado * ItemPedido.cantidad), 0
        )
        stmt = (
            select(
                Producto.id.label("producto_id"),
                Producto.nombre.label("nombre"),
                Producto.tipo_producto.label("tipo_producto"),
                ingreso.label("ingreso"),
                costo.label("costo_estimado"),
            )
            .join(ItemPedido, ItemPedido.producto_id == Producto.id)
            .join(Pedido, Pedido.id == ItemPedido.pedido_id)
            .where(Pedido.estado == EstadoPedido.ENTREGADO)
            .group_by(Producto.id, Producto.nombre, Producto.tipo_producto)
            .order_by((ingreso - costo).desc())
            .limit(limite)
        )
        filas = []
        for row in self.db.execute(stmt).all():
            ingreso_d = Decimal(str(row.ingreso or 0))
            costo_d = Decimal(str(row.costo_estimado or 0))
            utilidad = ingreso_d - costo_d
            margen = (
                (utilidad / ingreso_d * Decimal("100")) if ingreso_d != 0 else Decimal("0")
            )
            filas.append(
                {
                    "producto_id": int(row.producto_id),
                    "nombre": row.nombre,
                    "tipo_producto": row.tipo_producto,
                    "ingreso": ingreso_d,
                    "costo_estimado": costo_d,
                    "utilidad": utilidad,
                    "margen_porcentaje": margen,
                }
            )
        return filas

    def rentabilidad_pedidos(
        self,
        *,
        limite: int = 100,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[dict]:
        """Rentabilidad por pedido ENTREGADO (ingreso vs costo estimado de ítems)."""
        stmt = (
            select(Pedido)
            .where(Pedido.estado == EstadoPedido.ENTREGADO)
            .options(selectinload(Pedido.items))
            .order_by(Pedido.fecha_pedido.desc())
            .limit(limite)
        )
        if fecha_desde is not None:
            stmt = stmt.where(Pedido.fecha_pedido >= _inicio_dia(fecha_desde))
        if fecha_hasta is not None:
            stmt = stmt.where(Pedido.fecha_pedido <= _fin_dia(fecha_hasta))
        filas = []
        for pedido in self.db.scalars(stmt).all():
            costo = sum(
                (
                    Decimal(str(it.costo_unitario_estimado)) * Decimal(str(it.cantidad))
                    for it in pedido.items
                ),
                Decimal("0"),
            )
            ingreso = Decimal(str(pedido.total))
            utilidad = ingreso - costo
            margen = (
                (utilidad / ingreso * Decimal("100")) if ingreso != 0 else Decimal("0")
            )
            filas.append(
                {
                    "pedido_id": pedido.id,
                    "numero_pedido": pedido.numero_pedido,
                    "cliente_id": pedido.cliente_id,
                    "fecha_pedido": pedido.fecha_pedido.isoformat()
                    if pedido.fecha_pedido
                    else None,
                    "ingreso": ingreso,
                    "costo_estimado": costo,
                    "utilidad": utilidad,
                    "margen_porcentaje": margen,
                }
            )
        return filas

    # ------------------------------------------------------------------
    # Costos
    # ------------------------------------------------------------------

    def costos_produccion(
        self,
        *,
        etapa: str | None = None,
    ) -> list[dict]:
        """Asientos de costo de producción (ESTIMADO/REAL)."""
        stmt = (
            select(
                AsientoCostoProduccion.etapa_costo,
                CategoriaCosto.tipo_costo,
                CategoriaCosto.nombre.label("categoria"),
                func.coalesce(func.sum(AsientoCostoProduccion.costo_total), 0).label(
                    "total"
                ),
                func.count(AsientoCostoProduccion.id).label("cantidad_asientos"),
            )
            .join(
                CategoriaCosto,
                CategoriaCosto.id == AsientoCostoProduccion.categoria_costo_id,
            )
            .group_by(
                AsientoCostoProduccion.etapa_costo,
                CategoriaCosto.tipo_costo,
                CategoriaCosto.nombre,
            )
            .order_by(
                AsientoCostoProduccion.etapa_costo,
                CategoriaCosto.tipo_costo,
            )
        )
        if etapa is not None:
            stmt = stmt.where(AsientoCostoProduccion.etapa_costo == etapa)
        return [
            {
                "etapa_costo": row.etapa_costo,
                "tipo_costo": row.tipo_costo,
                "categoria": row.categoria,
                "total": Decimal(str(row.total or 0)),
                "cantidad_asientos": int(row.cantidad_asientos or 0),
            }
            for row in self.db.execute(stmt).all()
        ]

    def costos_por_categoria(self, *, etapa: str = EtapaCosto.REAL) -> list[dict]:
        """Costos agregados por tipo_costo (para gráficos)."""
        stmt = (
            select(
                CategoriaCosto.tipo_costo,
                func.coalesce(func.sum(AsientoCostoProduccion.costo_total), 0).label(
                    "total"
                ),
            )
            .join(
                CategoriaCosto,
                CategoriaCosto.id == AsientoCostoProduccion.categoria_costo_id,
            )
            .where(AsientoCostoProduccion.etapa_costo == etapa)
            .group_by(CategoriaCosto.tipo_costo)
            .order_by(func.sum(AsientoCostoProduccion.costo_total).desc())
        )
        return [
            {
                "tipo_costo": row.tipo_costo,
                "total": Decimal(str(row.total or 0)),
            }
            for row in self.db.execute(stmt).all()
        ]

    # ------------------------------------------------------------------
    # Compras / gastos
    # ------------------------------------------------------------------

    def reporte_compras(
        self,
        *,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[dict]:
        stmt = select(Compra).where(Compra.estado != "CANCELADA").order_by(Compra.id)
        if fecha_desde is not None:
            stmt = stmt.where(Compra.fecha_compra >= _inicio_dia(fecha_desde))
        if fecha_hasta is not None:
            stmt = stmt.where(Compra.fecha_compra <= _fin_dia(fecha_hasta))
        return [
            {
                "compra_id": c.id,
                "proveedor_id": c.proveedor_id,
                "numero_factura": c.numero_factura,
                "fecha_compra": c.fecha_compra.isoformat() if c.fecha_compra else None,
                "estado": c.estado,
                "subtotal": Decimal(str(c.subtotal)),
                "total": Decimal(str(c.total)),
            }
            for c in self.db.scalars(stmt).all()
        ]

    def reporte_gastos(
        self,
        *,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        excluir_vinculados_produccion: bool = True,
    ) -> list[dict]:
        vinculados = (
            self.gastos_repo.ids_vinculados_produccion()
            if excluir_vinculados_produccion
            else set()
        )
        stmt = (
            select(Gasto, CategoriaGasto.nombre)
            .join(CategoriaGasto, CategoriaGasto.id == Gasto.categoria_id)
            .where(Gasto.estado_pago != EstadoPagoGasto.ANULADO)
            .order_by(Gasto.fecha_gasto.desc())
        )
        if fecha_desde is not None:
            stmt = stmt.where(Gasto.fecha_gasto >= _inicio_dia(fecha_desde))
        if fecha_hasta is not None:
            stmt = stmt.where(Gasto.fecha_gasto <= _fin_dia(fecha_hasta))
        filas = []
        for gasto, cat_nombre in self.db.execute(stmt).all():
            if gasto.id in vinculados:
                continue
            filas.append(
                {
                    "gasto_id": gasto.id,
                    "categoria": cat_nombre,
                    "descripcion": gasto.descripcion,
                    "monto": Decimal(str(gasto.monto)),
                    "fecha_gasto": gasto.fecha_gasto.isoformat()
                    if gasto.fecha_gasto
                    else None,
                    "estado_pago": gasto.estado_pago,
                }
            )
        return filas

    # ------------------------------------------------------------------
    # Inventario
    # ------------------------------------------------------------------

    def inventario_valorizado(self) -> list[dict]:
        """Existencias valorizadas: materiales × costo_promedio; variantes × 0 (sin costo catálogo)."""
        filas: list[dict] = []
        # Materiales
        stmt_mat = (
            select(
                Existencia.id,
                Existencia.bodega_id,
                Bodega.nombre.label("bodega"),
                Material.id.label("material_id"),
                Material.nombre.label("articulo"),
                Material.costo_promedio,
                Existencia.cantidad,
            )
            .join(Bodega, Bodega.id == Existencia.bodega_id)
            .join(Material, Material.id == Existencia.material_id)
            .where(Existencia.material_id.is_not(None))
            .order_by(Bodega.nombre, Material.nombre)
        )
        for row in self.db.execute(stmt_mat).all():
            qty = Decimal(str(row.cantidad or 0))
            costo = Decimal(str(row.costo_promedio or 0))
            filas.append(
                {
                    "existencia_id": int(row.id),
                    "bodega_id": int(row.bodega_id),
                    "bodega": row.bodega,
                    "tipo_articulo": "MATERIAL",
                    "articulo_id": int(row.material_id),
                    "articulo": row.articulo,
                    "cantidad": qty,
                    "costo_unitario": costo,
                    "valor_total": qty * costo,
                }
            )
        # Variantes (productos terminados) — costo unitario 0 en V1 (sin costo promedio en variantes)
        stmt_var = (
            select(
                Existencia.id,
                Existencia.bodega_id,
                Bodega.nombre.label("bodega"),
                VarianteProducto.id.label("variante_id"),
                VarianteProducto.sku,
                Producto.nombre.label("producto"),
                Existencia.cantidad,
            )
            .join(Bodega, Bodega.id == Existencia.bodega_id)
            .join(
                VarianteProducto,
                VarianteProducto.id == Existencia.variante_producto_id,
            )
            .join(Producto, Producto.id == VarianteProducto.producto_id)
            .where(Existencia.variante_producto_id.is_not(None))
            .order_by(Bodega.nombre, VarianteProducto.sku)
        )
        for row in self.db.execute(stmt_var).all():
            qty = Decimal(str(row.cantidad or 0))
            filas.append(
                {
                    "existencia_id": int(row.id),
                    "bodega_id": int(row.bodega_id),
                    "bodega": row.bodega,
                    "tipo_articulo": "VARIANTE",
                    "articulo_id": int(row.variante_id),
                    "articulo": f"{row.producto} ({row.sku})",
                    "cantidad": qty,
                    "costo_unitario": Decimal("0"),
                    "valor_total": Decimal("0"),
                }
            )
        return filas

    def consumo_materiales(self) -> list[dict]:
        """Consumos de producción agregados por material."""
        stmt = (
            select(
                Material.id.label("material_id"),
                Material.nombre.label("nombre"),
                func.coalesce(func.sum(ConsumoProduccion.cantidad_consumida), 0).label(
                    "cantidad_consumida"
                ),
                func.coalesce(func.sum(ConsumoProduccion.costo_total), 0).label(
                    "costo_total"
                ),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                ConsumoProduccion.es_desperdicio.is_(True),
                                ConsumoProduccion.cantidad_consumida,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("cantidad_desperdicio"),
            )
            .join(Material, Material.id == ConsumoProduccion.material_id)
            .group_by(Material.id, Material.nombre)
            .order_by(func.sum(ConsumoProduccion.costo_total).desc())
        )
        return [
            {
                "material_id": int(row.material_id),
                "nombre": row.nombre,
                "cantidad_consumida": Decimal(str(row.cantidad_consumida or 0)),
                "cantidad_desperdicio": Decimal(str(row.cantidad_desperdicio or 0)),
                "costo_total": Decimal(str(row.costo_total or 0)),
            }
            for row in self.db.execute(stmt).all()
        ]

    def desperdicios(self) -> list[dict]:
        """Consumos marcados como desperdicio real."""
        stmt = (
            select(
                ConsumoProduccion.id,
                ConsumoProduccion.material_id,
                Material.nombre.label("material"),
                ConsumoProduccion.cantidad_consumida,
                ConsumoProduccion.costo_unitario_snapshot,
                ConsumoProduccion.costo_total,
                ConsumoProduccion.consumido_en,
                ConsumoProduccion.notas,
            )
            .join(Material, Material.id == ConsumoProduccion.material_id)
            .where(ConsumoProduccion.es_desperdicio.is_(True))
            .order_by(ConsumoProduccion.consumido_en.desc())
        )
        return [
            {
                "consumo_id": int(row.id),
                "material_id": int(row.material_id),
                "material": row.material,
                "cantidad": Decimal(str(row.cantidad_consumida or 0)),
                "costo_unitario": Decimal(str(row.costo_unitario_snapshot or 0)),
                "costo_total": Decimal(str(row.costo_total or 0)),
                "consumido_en": row.consumido_en.isoformat()
                if row.consumido_en
                else None,
                "notas": row.notas,
            }
            for row in self.db.execute(stmt).all()
        ]

    # ------------------------------------------------------------------
    # Dashboard helpers
    # ------------------------------------------------------------------

    def ventas_en_rango(self, desde: datetime, hasta: datetime) -> Decimal:
        valor = self.db.scalar(
            select(func.coalesce(func.sum(Pedido.total), 0)).where(
                Pedido.estado == EstadoPedido.ENTREGADO,
                Pedido.fecha_pedido >= desde,
                Pedido.fecha_pedido <= hasta,
            )
        )
        return Decimal(str(valor or 0))

    def dinero_recibido_en_rango(self, desde: datetime, hasta: datetime) -> Decimal:
        valor = self.db.scalar(
            select(func.coalesce(func.sum(Pago.monto), 0)).where(
                Pago.estado == EstadoPago.CONFIRMADO,
                Pago.fecha_pago >= desde,
                Pago.fecha_pago <= hasta,
            )
        )
        return Decimal(str(valor or 0))

    def gastos_en_rango(self, desde: datetime, hasta: datetime) -> Decimal:
        vinculados = self.gastos_repo.ids_vinculados_produccion()
        stmt = select(Gasto).where(
            Gasto.estado_pago != EstadoPagoGasto.ANULADO,
            Gasto.fecha_gasto >= desde,
            Gasto.fecha_gasto <= hasta,
        )
        total = Decimal("0")
        for g in self.db.scalars(stmt).all():
            if g.id in vinculados:
                continue
            total += Decimal(str(g.monto))
        return total

    def conteo_pedidos_por_estados(self, estados: list[str]) -> int:
        valor = self.db.scalar(
            select(func.count(Pedido.id)).where(Pedido.estado.in_(estados))
        )
        return int(valor or 0)

    def conteo_stock_bajo(self) -> int:
        """Materiales con suma de existencias < stock_minimo."""
        subq = (
            select(
                Material.id,
                Material.stock_minimo,
                func.coalesce(func.sum(Existencia.cantidad), 0).label("stock"),
            )
            .outerjoin(Existencia, Existencia.material_id == Material.id)
            .where(Material.activo.is_(True))
            .group_by(Material.id, Material.stock_minimo)
        ).subquery()
        valor = self.db.scalar(
            select(func.count()).select_from(subq).where(subq.c.stock < subq.c.stock_minimo)
        )
        return int(valor or 0)

    def evolucion_rentabilidad(self, *, meses: int = 6) -> list[dict]:
        """Utilidad mensual aproximada: ventas ENTREGADAS − costos REAL − gastos del mes."""
        ventas = {f["periodo"]: f["total_ventas"] for f in self.ventas_mensuales()}
        # Costos REAL por mes (creado_en del asiento)
        anio_c = extract("year", AsientoCostoProduccion.creado_en)
        mes_c = extract("month", AsientoCostoProduccion.creado_en)
        stmt_costos = (
            select(
                anio_c.label("anio"),
                mes_c.label("mes"),
                func.coalesce(func.sum(AsientoCostoProduccion.costo_total), 0).label(
                    "total"
                ),
            )
            .where(AsientoCostoProduccion.etapa_costo == EtapaCosto.REAL)
            .group_by(anio_c, mes_c)
        )
        costos: dict[str, Decimal] = {}
        for row in self.db.execute(stmt_costos).all():
            key = f"{int(row.anio):04d}-{int(row.mes):02d}"
            costos[key] = Decimal(str(row.total or 0))

        anio_g = extract("year", Gasto.fecha_gasto)
        mes_g = extract("month", Gasto.fecha_gasto)
        vinculados = self.gastos_repo.ids_vinculados_produccion()
        stmt_gastos = (
            select(Gasto, anio_g.label("anio"), mes_g.label("mes")).where(
                Gasto.estado_pago != EstadoPagoGasto.ANULADO
            )
        )
        gastos: dict[str, Decimal] = {}
        for gasto, anio, mes in self.db.execute(stmt_gastos).all():
            if gasto.id in vinculados:
                continue
            key = f"{int(anio):04d}-{int(mes):02d}"
            gastos[key] = gastos.get(key, Decimal("0")) + Decimal(str(gasto.monto))

        periodos = sorted(set(ventas) | set(costos) | set(gastos))
        if meses and len(periodos) > meses:
            periodos = periodos[-meses:]
        filas = []
        for p in periodos:
            v = ventas.get(p, Decimal("0"))
            c = costos.get(p, Decimal("0"))
            g = gastos.get(p, Decimal("0"))
            filas.append(
                {
                    "periodo": p,
                    "ventas": v,
                    "costos": c,
                    "gastos": g,
                    "utilidad": v - c - g,
                }
            )
        return filas
