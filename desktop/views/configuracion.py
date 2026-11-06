"""Vistas de configuración: categorías, unidades, métodos de pago, cuentas."""

from __future__ import annotations

import customtkinter as ctk

from desktop.api.client import ApiClient
from desktop.components.buttons import primary_button, secondary_button  # noqa: F401
from desktop.components.toast import ToastHost
from desktop.dialogs.form_dialog import FormDialog
from desktop.styles import theme
from desktop.views.base import BaseView, CrudListView


def build_datos_negocio_view(master, api: ApiClient, toast: ToastHost) -> BaseView:
    view = BaseView(
        master,
        api,
        toast,
        title="Datos del negocio",
        subtitle="Conexión con la API y estado del servicio",
    )
    secondary_button(view.toolbar, "Probar conexión", command=lambda: _probe(view)).pack(side="left")

    card = ctk.CTkFrame(
        view.body, fg_color=theme.SURFACE, corner_radius=10, border_width=1, border_color=theme.BORDER
    )
    card.pack(fill="x", pady=8)
    view.info = ctk.CTkLabel(
        card,
        text=f"URL API: {api.base_url}\nVariable: SUBLIMANAGER_API_URL",
        font=theme.FONT_BODY,
        text_color=theme.TEXT,
        justify="left",
        anchor="w",
    )
    view.info.pack(anchor="w", padx=16, pady=16)
    _probe(view)
    return view


def _probe(view: BaseView) -> None:
    def work():
        h = view.api.health()
        try:
            db = view.api.health_db()
        except Exception as exc:  # noqa: BLE001
            db = {"error": str(exc)}
        return h, db

    def ok(result) -> None:
        h, db = result
        view.info.configure(
            text=(
                f"URL API: {view.api.base_url}\n"
                f"Salud: {h}\n"
                f"Base de datos: {db}\n"
                "Variable: SUBLIMANAGER_API_URL"
            )
        )
        view.set_status("Conexión verificada")
        view.toast.show("API respondió correctamente", kind="success")

    view.run_api(work, on_success=ok, loading="Probando API…")


def build_categorias_view(master, api: ApiClient, toast: ToastHost) -> BaseView:
    view = BaseView(
        master,
        api,
        toast,
        title="Categorías",
        subtitle="Material, producto y gasto",
    )

    tabs = ctk.CTkTabview(view.body, fg_color=theme.BG)
    tabs.pack(fill="both", expand=True)
    tabs.add("Material")
    tabs.add("Producto")
    tabs.add("Gasto")

    def _embed(tab_name: str, title: str, list_fn, create_fn) -> None:
        frame = tabs.tab(tab_name)
        CrudListView(
            frame,
            api,
            toast,
            title=title,
            subtitle="",
            columns=[("id", "ID", 50), ("nombre", "Nombre", 200), ("activo", "Activo", 70)],
            fields=[
                ("nombre", "Nombre", "text"),
                ("descripcion", "Descripción", "textarea"),
                ("activo", "Activo", "bool"),
            ],
            list_fn=list_fn,
            create_fn=create_fn,
        ).pack(fill="both", expand=True)

    _embed("Material", "Categorías de material", api.listar_categorias_material, api.crear_categoria_material)
    _embed("Producto", "Categorías de producto", api.listar_categorias_producto, api.crear_categoria_producto)
    _embed("Gasto", "Categorías de gasto", api.listar_categorias_gasto, api.crear_categoria_gasto)
    return view


def build_unidades_view(master, api: ApiClient, toast: ToastHost) -> CrudListView:
    return CrudListView(
        master,
        api,
        toast,
        title="Unidades de medida",
        subtitle="Catálogo de unidades",
        columns=[
            ("id", "ID", 50),
            ("nombre", "Nombre", 160),
            ("abreviatura", "Abrev.", 80),
            ("activo", "Activo", 70),
        ],
        fields=[
            ("nombre", "Nombre", "text"),
            ("abreviatura", "Abreviatura", "text"),
            ("activo", "Activo", "bool"),
        ],
        list_fn=api.listar_unidades,
        create_fn=api.crear_unidad,
        update_fn=api.actualizar_unidad,
        delete_fn=api.eliminar_unidad,
    )


def build_metodos_pago_view(master, api: ApiClient, toast: ToastHost) -> CrudListView:
    return CrudListView(
        master,
        api,
        toast,
        title="Métodos de pago",
        subtitle="Efectivo, transferencia, Nequi, etc.",
        columns=[("id", "ID", 50), ("nombre", "Nombre", 200), ("activo", "Activo", 70)],
        fields=[("nombre", "Nombre", "text"), ("activo", "Activo", "bool")],
        list_fn=api.listar_metodos_pago,
        create_fn=api.crear_metodo_pago,
        update_fn=api.actualizar_metodo_pago,
        delete_fn=api.eliminar_metodo_pago,
    )


def build_cuentas_view(master, api: ApiClient, toast: ToastHost) -> CrudListView:
    tipos = [("EFECTIVO", "EFECTIVO"), ("BANCO", "BANCO")]

    def combos():
        return {"tipo_cuenta": tipos}

    # Also allow creating bodegas from here? Separate — cuentas de caja only.
    view = CrudListView(
        master,
        api,
        toast,
        title="Cuentas de caja",
        subtitle="Cuentas EFECTIVO / BANCO",
        columns=[
            ("id", "ID", 50),
            ("nombre", "Nombre", 180),
            ("tipo_cuenta", "Tipo", 100),
            ("activo", "Activo", 70),
        ],
        fields=[
            ("nombre", "Nombre", "text"),
            ("tipo_cuenta", "Tipo de cuenta", "combo"),
            ("activo", "Activo", "bool"),
        ],
        list_fn=api.listar_cuentas_caja,
        create_fn=api.crear_cuenta_caja,
        update_fn=api.actualizar_cuenta_caja,
        delete_fn=api.eliminar_cuenta_caja,
        combos_provider=combos,
    )

    def nueva_bodega() -> None:
        def submit(data: dict) -> None:
            view.run_api(
                lambda: api.crear_bodega(
                    {"nombre": data.get("nombre"), "ubicacion": data.get("ubicacion"), "activo": True}
                ),
                success_toast="Bodega creada",
                loading="Creando bodega…",
            )

        FormDialog(
            view,
            "Nueva bodega",
            [("nombre", "Nombre", "text"), ("ubicacion", "Ubicación", "text")],
            on_submit=submit,
            height=300,
        )

    primary_button(view.toolbar, "Nueva bodega", command=nueva_bodega).pack(side="left", padx=(8, 0))
    return view

