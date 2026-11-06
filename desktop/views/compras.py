"""Vistas Compras y Proveedores."""

from __future__ import annotations

from desktop.api.client import ApiClient
from desktop.components.buttons import danger_button, primary_button, secondary_button, success_button
from desktop.components.table import DataTable
from desktop.components.toast import ToastHost
from desktop.dialogs.confirm_dialog import ConfirmDialog
from desktop.dialogs.form_dialog import FormDialog
from desktop.views.base import BaseView, CrudListView


def build_proveedores_view(master, api: ApiClient, toast: ToastHost) -> CrudListView:
    return CrudListView(
        master,
        api,
        toast,
        title="Proveedores",
        subtitle="Catálogo de proveedores",
        columns=[
            ("id", "ID", 50),
            ("nombre", "Nombre", 180),
            ("identificacion", "Identificación", 120),
            ("telefono", "Teléfono", 110),
            ("email", "Email", 160),
            ("activo", "Activo", 70),
        ],
        fields=[
            ("nombre", "Nombre", "text"),
            ("identificacion", "Identificación", "text"),
            ("telefono", "Teléfono", "text"),
            ("email", "Email", "text"),
            ("direccion", "Dirección", "textarea"),
            ("activo", "Activo", "bool"),
        ],
        list_fn=api.listar_proveedores,
        create_fn=api.crear_proveedor,
        update_fn=api.actualizar_proveedor,
        delete_fn=api.eliminar_proveedor,
    )


def build_compras_view(master, api: ApiClient, toast: ToastHost) -> BaseView:
    view = BaseView(
        master,
        api,
        toast,
        title="Compras",
        subtitle="Órdenes de compra — recepción actualiza inventario vía API",
    )
    primary_button(view.toolbar, "Nueva compra", command=lambda: _nueva(view, api)).pack(side="left", padx=(0, 8))
    success_button(view.toolbar, "Recibir", command=lambda: _recibir(view, api)).pack(side="left", padx=(0, 8))
    danger_button(view.toolbar, "Cancelar", command=lambda: _cancelar(view, api)).pack(side="left", padx=(0, 8))
    secondary_button(view.toolbar, "Actualizar", command=lambda: _reload(view)).pack(side="left")

    view.table = DataTable(
        view.body,
        [
            ("id", "ID", 50),
            ("numero_factura", "Factura", 120),
            ("proveedor_id", "Proveedor", 90),
            ("total", "Total", 100),
            ("estado", "Estado", 100),
            ("fecha_compra", "Fecha", 160),
        ],
    )
    view.table.pack(fill="both", expand=True)
    _reload(view)
    return view


def _reload(view: BaseView) -> None:
    view.run_api(
        view.api.listar_compras,
        on_success=lambda rows: (view.table.set_rows(rows), view.set_status(f"{len(rows)} compra(s)")),
        loading="Cargando compras…",
    )


def _nueva(view: BaseView, api: ApiClient) -> None:
    try:
        proveedores = api.listar_proveedores()
        materiales = api.listar_materiales()
    except Exception as exc:  # noqa: BLE001
        view.toast.show(str(exc), kind="error")
        return

    def submit(data: dict) -> None:
        payload = {
            "proveedor_id": data.get("proveedor_id"),
            "numero_factura": data.get("numero_factura"),
            "items": [
                {
                    "material_id": data.get("material_id"),
                    "cantidad": data.get("cantidad"),
                    "costo_unitario": data.get("costo_unitario"),
                }
            ],
        }
        view.run_api(
            lambda: api.crear_compra(payload),
            on_success=lambda _r: _reload(view),
            loading="Creando compra…",
            success_toast="Compra creada en BORRADOR",
        )

    FormDialog(
        view,
        "Nueva compra",
        [
            ("proveedor_id", "Proveedor", "combo"),
            ("numero_factura", "Nº factura", "text"),
            ("material_id", "Material", "combo"),
            ("cantidad", "Cantidad", "float"),
            ("costo_unitario", "Costo unitario", "float"),
        ],
        combos={
            "proveedor_id": [(f"{p['id']} — {p['nombre']}", p["id"]) for p in proveedores],
            "material_id": [(f"{m['id']} — {m['nombre']}", m["id"]) for m in materiales],
        },
        on_submit=submit,
        height=480,
    )


def _recibir(view: BaseView, api: ApiClient) -> None:
    row = view.table.selected_row()
    if not row:
        view.toast.show("Seleccione una compra", kind="warning")
        return
    cid = int(row["id"])

    def confirm() -> None:
        view.run_api(
            lambda: api.recibir_compra(cid),
            on_success=lambda _r: _reload(view),
            loading="Recibiendo compra…",
            success_toast="Compra recibida — stock actualizado",
        )

    ConfirmDialog(
        view,
        "Recibir compra",
        "La recepción generará entrada de inventario y actualizará el costo promedio. ¿Continuar?",
        confirm_text="Recibir",
        on_confirm=confirm,
    )


def _cancelar(view: BaseView, api: ApiClient) -> None:
    row = view.table.selected_row()
    if not row:
        view.toast.show("Seleccione una compra", kind="warning")
        return
    cid = int(row["id"])

    def confirm() -> None:
        view.run_api(
            lambda: api.cancelar_compra(cid),
            on_success=lambda _r: _reload(view),
            loading="Cancelando…",
            success_toast="Compra cancelada",
        )

    ConfirmDialog(
        view,
        "Cancelar compra",
        "Solo se pueden cancelar compras en BORRADOR. ¿Continuar?",
        danger=True,
        confirm_text="Cancelar compra",
        on_confirm=confirm,
    )
