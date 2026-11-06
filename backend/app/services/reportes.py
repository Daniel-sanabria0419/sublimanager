"""ReportesService — agregaciones y exportaciones Stage 9 (§5.10).

Ventas = pedidos ENTREGADOS (no anticipos).
Utilidad estimada del dashboard = ventas_mes − costos_producción − gastos_mes.
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.repositories.finanzas import ConsultasFinancierasRepo
from app.repositories.reportes import ReportesRepo
from app.services.caja import CajaService
from app.utils.decimal_policy import money_round, percent_round
from app.utils.exportacion import generar_csv, generar_pdf

FormatoExport = Literal["csv", "pdf"]
TipoExport = Literal[
    "ventas",
    "inventario-valorizado",
    "rentabilidad-pedidos",
    "resumen-financiero",
]


def _money_rows(filas: list[dict], campos: list[str]) -> list[dict]:
    out = []
    for f in filas:
        g = dict(f)
        for c in campos:
            if c in g and g[c] is not None:
                g[c] = money_round(g[c])
        out.append(g)
    return out


class ReportesService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ReportesRepo(db)
        self.finanzas = ConsultasFinancierasRepo(db)
        self.caja = CajaService(db)

    # ---- Ventas ----
    def ventas_diarias(
        self,
        *,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[dict]:
        return _money_rows(
            self.repo.ventas_diarias(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta),
            ["total_ventas"],
        )

    def ventas_mensuales(self, *, anio: int | None = None) -> list[dict]:
        return _money_rows(self.repo.ventas_mensuales(anio=anio), ["total_ventas"])

    def productos_mas_vendidos(
        self,
        *,
        limite: int = 20,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[dict]:
        return _money_rows(
            self.repo.productos_mas_vendidos(
                limite=limite, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta
            ),
            ["total_ventas"],
        )

    def utilidad_por_producto(self, *, limite: int = 50) -> list[dict]:
        filas = self.repo.utilidad_por_producto(limite=limite)
        out = []
        for f in filas:
            out.append(
                {
                    **f,
                    "ingreso": money_round(f["ingreso"]),
                    "costo_estimado": money_round(f["costo_estimado"]),
                    "utilidad": money_round(f["utilidad"]),
                    "margen_porcentaje": percent_round(f["margen_porcentaje"]),
                }
            )
        return out

    def rentabilidad_pedidos(
        self,
        *,
        limite: int = 100,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[dict]:
        filas = self.repo.rentabilidad_pedidos(
            limite=limite, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta
        )
        out = []
        for f in filas:
            out.append(
                {
                    **f,
                    "ingreso": money_round(f["ingreso"]),
                    "costo_estimado": money_round(f["costo_estimado"]),
                    "utilidad": money_round(f["utilidad"]),
                    "margen_porcentaje": percent_round(f["margen_porcentaje"]),
                }
            )
        return out

    # ---- Costos ----
    def costos_produccion(self, *, etapa: str | None = None) -> list[dict]:
        return _money_rows(self.repo.costos_produccion(etapa=etapa), ["total"])

    def costos_por_categoria(self, *, etapa: str = "REAL") -> list[dict]:
        return _money_rows(self.repo.costos_por_categoria(etapa=etapa), ["total"])

    # ---- Compras / gastos ----
    def compras(
        self,
        *,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[dict]:
        return _money_rows(
            self.repo.reporte_compras(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta),
            ["subtotal", "total"],
        )

    def gastos(
        self,
        *,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[dict]:
        return _money_rows(
            self.repo.reporte_gastos(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta),
            ["monto"],
        )

    # ---- Inventario / consumo ----
    def inventario_valorizado(self) -> list[dict]:
        return _money_rows(
            self.repo.inventario_valorizado(),
            ["costo_unitario", "valor_total"],
        )

    def consumo_materiales(self) -> list[dict]:
        return _money_rows(self.repo.consumo_materiales(), ["costo_total"])

    def desperdicios(self) -> list[dict]:
        return _money_rows(
            self.repo.desperdicios(),
            ["costo_unitario", "costo_total"],
        )

    # ---- CxC / CxP wrap ----
    def cuentas_pendientes(self) -> dict:
        cxc = self.caja.cuentas_por_cobrar()
        cxp = self.caja.cuentas_por_pagar()
        return {
            "cuentas_por_cobrar": cxc,
            "cuentas_por_pagar": cxp,
            "total_cxc": money_round(sum((f["saldo_pendiente"] for f in cxc), Decimal("0"))),
            "total_cxp": money_round(sum((f["saldo_pendiente"] for f in cxp), Decimal("0"))),
        }

    # ---- Dashboard ----
    def dashboard(self) -> dict:
        hoy = datetime.now(timezone.utc).date()
        inicio_dia = datetime.combine(hoy, time.min, tzinfo=timezone.utc)
        fin_dia = datetime.combine(hoy, time.max, tzinfo=timezone.utc)
        inicio_mes = datetime(hoy.year, hoy.month, 1, tzinfo=timezone.utc)

        ventas_dia = money_round(self.repo.ventas_en_rango(inicio_dia, fin_dia))
        ventas_mes = money_round(self.repo.ventas_en_rango(inicio_mes, fin_dia))
        dinero = money_round(self.finanzas.dinero_recibido_clientes())
        cxc = money_round(self.finanzas.total_cxc())
        gastos_mes = money_round(self.repo.gastos_en_rango(inicio_mes, fin_dia))
        costos = money_round(self.finanzas.costos_produccion_reales())
        utilidad_estimada = money_round(ventas_mes - costos - gastos_mes)
        resumen = self.caja.resumen_financiero()

        pendientes = self.repo.conteo_pedidos_por_estados(
            ["PENDIENTE", "CONFIRMADO", "DISENO", "ESPERANDO_APROBACION"]
        )
        en_prod = self.repo.conteo_pedidos_por_estados(["EN_PRODUCCION"])
        listos = self.repo.conteo_pedidos_por_estados(["LISTO"])
        stock_bajo = self.repo.conteo_stock_bajo()

        evolucion = []
        for f in self.repo.evolucion_rentabilidad(meses=6):
            evolucion.append(
                {
                    "periodo": f["periodo"],
                    "ventas": money_round(f["ventas"]),
                    "costos": money_round(f["costos"]),
                    "gastos": money_round(f["gastos"]),
                    "utilidad": money_round(f["utilidad"]),
                }
            )

        return {
            "ventas_dia": ventas_dia,
            "ventas_mes": ventas_mes,
            "dinero_recibido": dinero,
            "pedidos_pendientes": pendientes,
            "pedidos_en_produccion": en_prod,
            "pedidos_listos": listos,
            "cuentas_por_cobrar": cxc,
            "gastos_mes": gastos_mes,
            "utilidad_estimada": utilidad_estimada,
            "stock_bajo": stock_bajo,
            "costos_produccion": costos,
            "utilidad_operativa": resumen["utilidad_operativa"],
            "ingresos_vs_gastos": evolucion,
            "ventas_por_dia": self.ventas_diarias(),
            "productos_mas_vendidos": self.productos_mas_vendidos(limite=10),
            "costos_por_categoria": self.costos_por_categoria(),
            "notas": (
                "Ventas = pedidos ENTREGADOS. Dinero recibido = pagos CONFIRMADOS. "
                "Utilidad estimada (mes) = ventas_mes − costos REAL − gastos_mes. "
                "Gastos excluyen ligados a OP (gasto_id)."
            ),
        }

    # ---- Export ----
    def exportar(
        self,
        tipo: TipoExport,
        *,
        formato: FormatoExport = "csv",
    ) -> tuple[bytes, str, str]:
        """Devuelve (contenido, media_type, filename)."""
        if tipo == "ventas":
            filas = self.ventas_diarias()
            cols = ["fecha", "cantidad_pedidos", "total_ventas"]
            headers = ["Fecha", "Cantidad pedidos", "Total ventas"]
            titulo = "Ventas diarias"
            notas = "Solo pedidos en estado ENTREGADO."
        elif tipo == "inventario-valorizado":
            filas = self.inventario_valorizado()
            cols = [
                "bodega",
                "tipo_articulo",
                "articulo",
                "cantidad",
                "costo_unitario",
                "valor_total",
            ]
            headers = [
                "Bodega",
                "Tipo",
                "Artículo",
                "Cantidad",
                "Costo unitario",
                "Valor total",
            ]
            titulo = "Inventario valorizado"
            notas = "Materiales valorizados con costo_promedio."
        elif tipo == "rentabilidad-pedidos":
            filas = self.rentabilidad_pedidos()
            cols = [
                "numero_pedido",
                "fecha_pedido",
                "ingreso",
                "costo_estimado",
                "utilidad",
                "margen_porcentaje",
            ]
            headers = [
                "Pedido",
                "Fecha",
                "Ingreso",
                "Costo estimado",
                "Utilidad",
                "Margen %",
            ]
            titulo = "Rentabilidad por pedido"
            notas = "Pedidos ENTREGADOS; costo = snapshot estimado de ítems."
        elif tipo == "resumen-financiero":
            resumen = self.caja.resumen_financiero()
            filas = [
                {"concepto": k, "valor": v}
                for k, v in resumen.items()
                if k != "notas"
            ]
            cols = ["concepto", "valor"]
            headers = ["Concepto", "Valor"]
            titulo = "Resumen financiero"
            notas = str(resumen.get("notas", ""))
        else:
            raise ValueError(f"Tipo de exportación no soportado: {tipo}")

        if formato == "csv":
            content = generar_csv(cols, filas, encabezados=headers)
            media = "text/csv; charset=utf-8"
            filename = f"reporte-{tipo}.csv"
        elif formato == "pdf":
            content = generar_pdf(
                titulo, cols, filas, encabezados=headers, notas=notas
            )
            media = "application/pdf"
            filename = f"reporte-{tipo}.pdf"
        else:
            raise ValueError(f"Formato no soportado: {formato}")
        return content, media, filename
