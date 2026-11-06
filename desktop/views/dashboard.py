"""Dashboard — KPIs y gráficos desde /api/v1/reportes/dashboard."""

from __future__ import annotations

import customtkinter as ctk

from desktop.api.client import ApiClient
from desktop.components.buttons import secondary_button
from desktop.components.cards import KpiCard
from desktop.components.charts import ChartPanel
from desktop.components.toast import ToastHost
from desktop.styles import theme
from desktop.views.base import BaseView


def _money(value) -> str:
    try:
        return f"$ {float(value):,.2f}"
    except (TypeError, ValueError):
        return "—"


def _num(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class DashboardView(BaseView):
    def __init__(self, master, api: ApiClient, toast: ToastHost, **kwargs) -> None:
        super().__init__(
            master,
            api,
            toast,
            title="Dashboard",
            subtitle="KPIs y gráficos con datos reales del API (Etapa 9)",
            **kwargs,
        )
        secondary_button(self.toolbar, "Actualizar", command=self.reload).pack(side="left")

        grid = ctk.CTkFrame(self.body, fg_color="transparent")
        grid.pack(fill="x", pady=(8, 12))
        for i in range(4):
            grid.grid_columnconfigure(i, weight=1)

        self.kpis = {
            "ventas_dia": KpiCard(grid, "Ventas del día", accent=theme.PRIMARY),
            "ventas_mes": KpiCard(grid, "Ventas del mes", accent=theme.PRIMARY),
            "cobrado": KpiCard(grid, "Dinero recibido", accent=theme.SUCCESS),
            "utilidad": KpiCard(grid, "Utilidad estimada (mes)", accent=theme.SUCCESS),
        }
        for i, card in enumerate(self.kpis.values()):
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0))

        self.kpis2 = {
            "pendientes": KpiCard(grid, "Pedidos pendientes", accent=theme.WARNING),
            "produccion": KpiCard(grid, "En producción", accent=theme.PRIMARY),
            "listos": KpiCard(grid, "Listos", accent=theme.SUCCESS),
            "cxc": KpiCard(grid, "Cuentas por cobrar", accent=theme.WARNING),
        }
        for i, card in enumerate(self.kpis2.values()):
            card.grid(row=1, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0), pady=(8, 0))

        self.kpis3 = {
            "gastos": KpiCard(grid, "Gastos del mes", accent=theme.ERROR),
            "stock": KpiCard(grid, "Stock bajo", accent=theme.WARNING),
            "operativa": KpiCard(grid, "Utilidad operativa", accent=theme.PRIMARY),
            "costos": KpiCard(grid, "Costos producción", accent=theme.ERROR),
        }
        for i, card in enumerate(self.kpis3.values()):
            card.grid(row=2, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0), pady=(8, 0))

        charts = ctk.CTkScrollableFrame(self.body, fg_color="transparent")
        charts.pack(fill="both", expand=True, pady=(8, 0))
        for i in range(2):
            charts.grid_columnconfigure(i, weight=1)

        self.chart_ventas = ChartPanel(charts, "Ventas por día")
        self.chart_ventas.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        self.chart_ing_gas = ChartPanel(charts, "Ingresos vs gastos (evolución)")
        self.chart_ing_gas.grid(row=0, column=1, sticky="nsew", pady=(0, 8))
        self.chart_top = ChartPanel(charts, "Productos más vendidos")
        self.chart_top.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        self.chart_costos = ChartPanel(charts, "Costos por categoría")
        self.chart_costos.grid(row=1, column=1, sticky="nsew", pady=(0, 8))
        self.chart_rent = ChartPanel(charts, "Evolución de rentabilidad")
        self.chart_rent.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 8))

        self.reload()

    def reload(self) -> None:
        def work():
            return self.api.dashboard_reportes()

        def ok(data: dict) -> None:
            self.kpis["ventas_dia"].set_value(_money(data.get("ventas_dia")))
            self.kpis["ventas_mes"].set_value(_money(data.get("ventas_mes")))
            self.kpis["cobrado"].set_value(_money(data.get("dinero_recibido")))
            self.kpis["utilidad"].set_value(_money(data.get("utilidad_estimada")))
            self.kpis2["pendientes"].set_value(str(data.get("pedidos_pendientes", 0)))
            self.kpis2["produccion"].set_value(str(data.get("pedidos_en_produccion", 0)))
            self.kpis2["listos"].set_value(str(data.get("pedidos_listos", 0)))
            self.kpis2["cxc"].set_value(_money(data.get("cuentas_por_cobrar")))
            self.kpis3["gastos"].set_value(_money(data.get("gastos_mes")))
            self.kpis3["stock"].set_value(str(data.get("stock_bajo", 0)))
            self.kpis3["operativa"].set_value(_money(data.get("utilidad_operativa")))
            self.kpis3["costos"].set_value(_money(data.get("costos_produccion")))

            ventas_dia = data.get("ventas_por_dia") or []
            self.chart_ventas.plot_bars(
                [str(r.get("fecha", ""))[-5:] for r in ventas_dia],
                [_num(r.get("total_ventas")) for r in ventas_dia],
                color=theme.PRIMARY,
            )

            evo = data.get("ingresos_vs_gastos") or []
            labels = [str(r.get("periodo", "")) for r in evo]
            self.chart_ing_gas.plot_lines(
                labels,
                {
                    "Ventas": [_num(r.get("ventas")) for r in evo],
                    "Gastos": [_num(r.get("gastos")) for r in evo],
                },
                colors={"Ventas": theme.SUCCESS, "Gastos": theme.ERROR},
            )
            self.chart_rent.plot_lines(
                labels,
                {"Utilidad": [_num(r.get("utilidad")) for r in evo]},
                colors={"Utilidad": theme.PRIMARY},
            )

            top = data.get("productos_mas_vendidos") or []
            self.chart_top.plot_bars(
                [str(r.get("nombre", ""))[:18] for r in top],
                [_num(r.get("cantidad_vendida")) for r in top],
                color=theme.WARNING,
            )

            costos = data.get("costos_por_categoria") or []
            self.chart_costos.plot_bars(
                [str(r.get("tipo_costo", "")) for r in costos],
                [_num(r.get("total")) for r in costos],
                color=theme.ERROR,
            )
            self.set_status("Dashboard actualizado desde /reportes/dashboard")

        self.run_api(work, on_success=ok, loading="Cargando dashboard…")
