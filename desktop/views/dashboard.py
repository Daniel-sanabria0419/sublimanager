"""Dashboard — KPIs desde /finanzas/resumen y listados Stage 7."""

from __future__ import annotations

import customtkinter as ctk

from desktop.api.client import ApiClient
from desktop.components.buttons import secondary_button
from desktop.components.cards import KpiCard, SurfaceCard
from desktop.components.toast import ToastHost
from desktop.styles import theme
from desktop.views.base import BaseView


def _money(value) -> str:
    try:
        return f"$ {float(value):,.2f}"
    except (TypeError, ValueError):
        return "—"


class DashboardView(BaseView):
    def __init__(self, master, api: ApiClient, toast: ToastHost, **kwargs) -> None:
        super().__init__(
            master,
            api,
            toast,
            title="Dashboard",
            subtitle="Resumen financiero y operativa (datos reales del API)",
            **kwargs,
        )
        secondary_button(self.toolbar, "Actualizar", command=self.reload).pack(side="left")

        grid = ctk.CTkFrame(self.body, fg_color="transparent")
        grid.pack(fill="x", pady=(8, 12))
        for i in range(4):
            grid.grid_columnconfigure(i, weight=1)

        self.kpis = {
            "ventas": KpiCard(grid, "Ventas reconocidas", accent=theme.PRIMARY),
            "cobrado": KpiCard(grid, "Dinero recibido", accent=theme.SUCCESS),
            "cxc": KpiCard(grid, "Cuentas por cobrar", accent=theme.WARNING),
            "utilidad": KpiCard(grid, "Utilidad operativa", accent=theme.PRIMARY),
        }
        for i, card in enumerate(self.kpis.values()):
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0))

        self.kpis2 = {
            "gastos": KpiCard(grid, "Gastos operativos", accent=theme.ERROR),
            "caja": KpiCard(grid, "Saldo de caja neto", accent=theme.SUCCESS),
            "pedidos": KpiCard(grid, "Pedidos abiertos", accent=theme.PRIMARY),
            "alertas": KpiCard(grid, "Alertas de stock", accent=theme.WARNING),
        }
        for i, card in enumerate(self.kpis2.values()):
            card.grid(row=1, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0), pady=(8, 0))

        note = SurfaceCard(self.body)
        note.pack(fill="both", expand=True, pady=(8, 0))
        ctk.CTkLabel(
            note,
            text="Gráficos y reportes detallados llegan en la Etapa 9. "
            "Este panel consume /api/v1/finanzas/resumen, pedidos y alertas de stock.",
            font=theme.FONT_BODY,
            text_color=theme.TEXT_MUTED,
            wraplength=720,
            justify="left",
        ).pack(anchor="w", padx=16, pady=16)

        self.reload()

    def reload(self) -> None:
        def work():
            resumen = self.api.resumen_financiero()
            pedidos = self.api.listar_pedidos()
            abiertos = [
                p
                for p in pedidos
                if p.get("estado") not in ("ENTREGADO", "CANCELADO")
            ]
            try:
                alertas = self.api.alertas_stock_bajo()
            except Exception:
                alertas = []
            return resumen, abiertos, alertas

        def ok(result) -> None:
            resumen, abiertos, alertas = result
            self.kpis["ventas"].set_value(_money(resumen.get("ventas_reconocidas")))
            self.kpis["cobrado"].set_value(_money(resumen.get("dinero_recibido")))
            self.kpis["cxc"].set_value(_money(resumen.get("cuentas_por_cobrar")))
            self.kpis["utilidad"].set_value(_money(resumen.get("utilidad_operativa")))
            self.kpis2["gastos"].set_value(_money(resumen.get("gastos_operativos")))
            self.kpis2["caja"].set_value(_money(resumen.get("saldo_caja_neto")))
            self.kpis2["pedidos"].set_value(str(len(abiertos)))
            self.kpis2["alertas"].set_value(str(len(alertas)))
            self.set_status("Datos actualizados desde la API")

        self.run_api(work, on_success=ok, loading="Cargando dashboard…")
