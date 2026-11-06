"""Vista Productos."""

from __future__ import annotations

from desktop.api.client import ApiClient
from desktop.components.buttons import secondary_button
from desktop.components.toast import ToastHost
from desktop.dialogs.form_dialog import FormDialog
from desktop.views.base import CrudListView


TIPOS = [("FABRICADO", "FABRICADO"), ("REVENTA", "REVENTA"), ("SERVICIO", "SERVICIO")]


def build_productos_view(master, api: ApiClient, toast: ToastHost) -> CrudListView:
    def combos():
        cats = api.listar_categorias_producto()
        return {
            "categoria_id": [(f"{c['id']} — {c['nombre']}", c["id"]) for c in cats] or [("—", None)],
            "tipo_producto": TIPOS,
        }

    view = CrudListView(
        master,
        api,
        toast,
        title="Productos",
        subtitle="Catálogo de productos FABRICADO / REVENTA / SERVICIO",
        columns=[
            ("id", "ID", 50),
            ("nombre", "Nombre", 200),
            ("tipo_producto", "Tipo", 100),
            ("categoria_id", "Categoría", 90),
            ("activo", "Activo", 70),
        ],
        fields=[
            ("categoria_id", "Categoría", "combo"),
            ("nombre", "Nombre", "text"),
            ("descripcion", "Descripción", "textarea"),
            ("tipo_producto", "Tipo", "combo"),
            ("activo", "Activo", "bool"),
        ],
        list_fn=api.listar_productos,
        create_fn=api.crear_producto,
        update_fn=api.actualizar_producto,
        combos_provider=combos,
    )

    def ver_costo() -> None:
        row = view.table.selected_row()
        if not row:
            toast.show("Seleccione un producto", kind="warning")
            return
        pid = int(row["id"])

        def ok(data) -> None:
            toast.show(
                f"Costo estimado: {data.get('costo_estimado')} · "
                f"Utilidad: {data.get('utilidad')} · Margen: {data.get('margen_porcentaje')}%",
                kind="info",
                duration_ms=6000,
            )

        view.run_api(lambda: api.costo_estimado(pid), on_success=ok, loading="Calculando costo…")

    def nueva_variante() -> None:
        row = view.table.selected_row()
        if not row:
            toast.show("Seleccione un producto", kind="warning")
            return
        pid = int(row["id"])

        def submit(data: dict) -> None:
            payload = {
                "producto_id": pid,
                "sku": data.get("sku"),
                "talla": data.get("talla"),
                "color": data.get("color"),
                "precio_venta": data.get("precio_venta"),
                "control_stock": bool(data.get("control_stock", True)),
                "activo": True,
            }
            view.run_api(
                lambda: api.crear_variante(payload),
                on_success=lambda _r: toast.show("Variante creada", kind="success"),
                loading="Creando variante…",
            )

        FormDialog(
            view,
            "Nueva variante",
            [
                ("sku", "SKU", "text"),
                ("talla", "Talla", "text"),
                ("color", "Color", "text"),
                ("precio_venta", "Precio de venta", "float"),
                ("control_stock", "Controla stock", "bool"),
            ],
            on_submit=submit,
            height=420,
        )

    secondary_button(view.toolbar, "Costo estimado", command=ver_costo).pack(side="left", padx=(8, 0))
    secondary_button(view.toolbar, "Nueva variante", command=nueva_variante).pack(side="left", padx=(8, 0))
    return view
