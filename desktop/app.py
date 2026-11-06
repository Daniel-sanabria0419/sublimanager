"""Shell ERP: sidebar + top bar + área de contenido."""

from __future__ import annotations

import customtkinter as ctk

from desktop.api.client import ApiClient
from desktop.components.toast import ToastHost
from desktop.styles import theme
from desktop.views import (
    clientes,
    compras,
    configuracion,
    dashboard,
    finanzas,
    inventario,
    pedidos,
    produccion,
    productos,
    reportes,
)


class SubliManagerApp(ctk.CTk):
    def __init__(self, api: ApiClient | None = None) -> None:
        super().__init__()
        self.title("SubliManager")
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.configure(fg_color=theme.BG)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.api = api or ApiClient()
        self._current_key: str | None = None
        self._nav_buttons: dict[str, ctk.CTkButton] = {}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.show_view("dashboard")
        self.after(200, self._check_api)

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=240, fg_color=theme.SIDEBAR, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)

        brand = ctk.CTkLabel(
            sidebar,
            text="SubliManager",
            font=(theme.FONT_FAMILY, 18, "bold"),
            text_color="#FFFFFF",
        )
        brand.pack(anchor="w", padx=18, pady=(22, 4))
        ctk.CTkLabel(
            sidebar,
            text="ERP de sublimación",
            font=theme.FONT_SMALL,
            text_color="#94A3B8",
        ).pack(anchor="w", padx=18, pady=(0, 16))

        scroll = ctk.CTkScrollableFrame(sidebar, fg_color=theme.SIDEBAR, scrollbar_button_color=theme.SIDEBAR_HOVER)
        scroll.pack(fill="both", expand=True, padx=8, pady=(0, 12))

        for section, items in theme.MENU_SECTIONS:
            ctk.CTkLabel(
                scroll,
                text=section,
                font=theme.FONT_SIDEBAR_SECTION,
                text_color="#94A3B8",
                anchor="w",
            ).pack(fill="x", padx=10, pady=(12, 4))
            for key, label in items:
                btn = ctk.CTkButton(
                    scroll,
                    text=f"  {label}",
                    anchor="w",
                    height=32,
                    fg_color="transparent",
                    hover_color=theme.SIDEBAR_HOVER,
                    text_color="#E2E8F0",
                    font=theme.FONT_SIDEBAR,
                    command=lambda k=key: self.show_view(k),
                )
                btn.pack(fill="x", padx=4, pady=1)
                self._nav_buttons[key] = btn

    def _build_main(self) -> None:
        main = ctk.CTkFrame(self, fg_color=theme.BG, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(main, height=56, fg_color=theme.SURFACE, corner_radius=0)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_propagate(False)

        self._title_label = ctk.CTkLabel(
            top, text="Dashboard", font=theme.FONT_SECTION, text_color=theme.TEXT
        )
        self._title_label.pack(side="left", padx=20)

        self._api_label = ctk.CTkLabel(
            top, text=f"API · {self.api.base_url}", font=theme.FONT_SMALL, text_color=theme.TEXT_MUTED
        )
        self._api_label.pack(side="right", padx=20)

        content_wrap = ctk.CTkFrame(main, fg_color=theme.BG, corner_radius=0)
        content_wrap.grid(row=1, column=0, sticky="nsew")
        content_wrap.grid_rowconfigure(0, weight=1)
        content_wrap.grid_columnconfigure(0, weight=1)

        self.content = ctk.CTkFrame(content_wrap, fg_color=theme.BG, corner_radius=0)
        self.content.grid(row=0, column=0, sticky="nsew")

        self.toast = ToastHost(content_wrap)
        self.toast.place(relx=1.0, rely=0.0, anchor="ne", x=-16, y=12)

    def show_view(self, key: str) -> None:
        if key == self._current_key:
            return
        self._current_key = key
        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(fg_color=theme.SIDEBAR_ACTIVE, text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color="#E2E8F0")

        for child in self.content.winfo_children():
            child.destroy()

        builders = {
            "dashboard": dashboard.DashboardView,
            "pedidos": pedidos.build_pedidos_view,
            "clientes": clientes.build_clientes_view,
            "productos": productos.build_productos_view,
            "ordenes_produccion": produccion.build_ordenes_view,
            "recetas": produccion.build_recetas_view,
            "seguimiento": produccion.build_seguimiento_view,
            "insumos": inventario.build_insumos_view,
            "productos_terminados": inventario.build_productos_terminados_view,
            "movimientos": inventario.build_movimientos_view,
            "compras": compras.build_compras_view,
            "proveedores": compras.build_proveedores_view,
            "finanzas_resumen": finanzas.build_resumen_view,
            "ingresos": finanzas.build_ingresos_view,
            "gastos": finanzas.build_gastos_view,
            "cuentas_por_cobrar": finanzas.build_cxc_view,
            "cuentas_por_pagar": finanzas.build_cxp_view,
            "caja": finanzas.build_caja_view,
            "reportes": reportes.build_reportes_view,
            "datos_negocio": configuracion.build_datos_negocio_view,
            "categorias": configuracion.build_categorias_view,
            "unidades": configuracion.build_unidades_view,
            "metodos_pago": configuracion.build_metodos_pago_view,
            "cuentas": configuracion.build_cuentas_view,
        }
        builder = builders.get(key)
        titles = {k: label for _, items in theme.MENU_SECTIONS for k, label in items}
        self._title_label.configure(text=titles.get(key, key))

        if builder is None:
            ctk.CTkLabel(
                self.content, text="Vista no disponible", text_color=theme.TEXT_MUTED
            ).pack(pady=40)
            return

        view = builder(self.content, self.api, self.toast)
        view.pack(fill="both", expand=True)

    def _check_api(self) -> None:
        from desktop.utils.async_ui import run_async

        def work():
            return self.api.health()

        def ok(_data) -> None:
            self._api_label.configure(text=f"API conectada · {self.api.base_url}", text_color=theme.SUCCESS)

        def err(exc: Exception) -> None:
            self._api_label.configure(
                text=f"API no disponible · {self.api.base_url}", text_color=theme.ERROR
            )
            self.toast.show(str(exc), kind="warning", duration_ms=5000)

        run_async(self, work, on_success=ok, on_error=err)

    def _on_close(self) -> None:
        try:
            self.api.close()
        except Exception:
            pass
        self.destroy()
