"""Vista Pedidos — listado, alta, cambio de estado, anticipos."""

from __future__ import annotations

from desktop.api.client import ApiClient
from desktop.components.buttons import danger_button, primary_button, secondary_button, success_button
from desktop.components.table import DataTable
from desktop.components.toast import ToastHost
from desktop.dialogs.confirm_dialog import ConfirmDialog
from desktop.dialogs.form_dialog import FormDialog
from desktop.views.base import BaseView

ESTADOS = [
    "PENDIENTE",
    "CONFIRMADO",
    "DISENO",
    "ESPERANDO_APROBACION",
    "EN_PRODUCCION",
    "LISTO",
    "ENTREGADO",
]


def build_pedidos_view(master, api: ApiClient, toast: ToastHost) -> BaseView:
    view = BaseView(
        master,
        api,
        toast,
        title="Pedidos",
        subtitle="Pedidos de clientes — estados y anticipos vía API",
    )
    primary_button(view.toolbar, "Nuevo pedido", command=lambda: _nuevo(view, api)).pack(side="left", padx=(0, 8))
    secondary_button(view.toolbar, "Cambiar estado", command=lambda: _estado(view, api)).pack(side="left", padx=(0, 8))
    success_button(view.toolbar, "Registrar pago", command=lambda: _pago(view, api)).pack(side="left", padx=(0, 8))
    danger_button(view.toolbar, "Cancelar", command=lambda: _cancelar(view, api)).pack(side="left", padx=(0, 8))
    secondary_button(view.toolbar, "Actualizar", command=lambda: _reload(view)).pack(side="left")

    view.table = DataTable(
        view.body,
        [
            ("id", "ID", 50),
            ("numero_pedido", "Número", 110),
            ("cliente_id", "Cliente", 80),
            ("estado", "Estado", 130),
            ("total", "Total", 90),
            ("total_pagado", "Pagado", 90),
            ("saldo_pendiente", "Saldo", 90),
        ],
    )
    view.table.pack(fill="both", expand=True)
    _reload(view)
    return view


def _reload(view: BaseView) -> None:
    view.run_api(
        view.api.listar_pedidos,
        on_success=lambda rows: (view.table.set_rows(rows), view.set_status(f"{len(rows)} pedido(s)")),
        loading="Cargando pedidos…",
    )


def _nuevo(view: BaseView, api: ApiClient) -> None:
    try:
        clientes = api.listar_clientes()
        productos = api.listar_productos()
    except Exception as exc:  # noqa: BLE001
        view.toast.show(str(exc), kind="error")
        return

    def submit(data: dict) -> None:
        payload = {
            "cliente_id": data.get("cliente_id"),
            "numero_pedido": data.get("numero_pedido"),
            "descuento": data.get("descuento") or 0,
            "notas": data.get("notas"),
            "items": [
                {
                    "producto_id": data.get("producto_id"),
                    "cantidad": data.get("cantidad"),
                    "precio_venta_unitario": data.get("precio_venta_unitario"),
                    "descripcion": data.get("descripcion_item"),
                }
            ],
        }
        view.run_api(
            lambda: api.crear_pedido(payload),
            on_success=lambda _r: _reload(view),
            loading="Creando pedido…",
            success_toast="Pedido creado",
        )

    FormDialog(
        view,
        "Nuevo pedido",
        [
            ("cliente_id", "Cliente", "combo"),
            ("numero_pedido", "Número (opcional)", "text"),
            ("producto_id", "Producto", "combo"),
            ("cantidad", "Cantidad", "float"),
            ("precio_venta_unitario", "Precio unitario", "float"),
            ("descripcion_item", "Descripción ítem", "text"),
            ("descuento", "Descuento (monto)", "float"),
            ("notas", "Notas", "textarea"),
        ],
        combos={
            "cliente_id": [(f"{c['id']} — {c['nombre']}", c["id"]) for c in clientes],
            "producto_id": [(f"{p['id']} — {p['nombre']}", p["id"]) for p in productos],
        },
        on_submit=submit,
        height=620,
    )


def _estado(view: BaseView, api: ApiClient) -> None:
    row = view.table.selected_row()
    if not row:
        view.toast.show("Seleccione un pedido", kind="warning")
        return
    pid = int(row["id"])

    def submit(data: dict) -> None:
        view.run_api(
            lambda: api.cambiar_estado_pedido(pid, data.get("estado"), data.get("notas")),
            on_success=lambda _r: _reload(view),
            loading="Cambiando estado…",
            success_toast="Estado actualizado",
        )

    FormDialog(
        view,
        "Cambiar estado",
        [
            ("estado", "Nuevo estado", "combo"),
            ("notas", "Notas", "textarea"),
        ],
        combos={"estado": [(e, e) for e in ESTADOS]},
        initial={"estado": row.get("estado")},
        on_submit=submit,
        height=320,
    )


def _pago(view: BaseView, api: ApiClient) -> None:
    row = view.table.selected_row()
    if not row:
        view.toast.show("Seleccione un pedido", kind="warning")
        return
    pid = int(row["id"])
    try:
        metodos = api.listar_metodos_pago()
        cuentas = api.listar_cuentas_caja()
    except Exception as exc:  # noqa: BLE001
        view.toast.show(str(exc), kind="error")
        return

    def submit(data: dict) -> None:
        payload = {
            "pedido_id": pid,
            "metodo_pago_id": data.get("metodo_pago_id"),
            "cuenta_caja_id": data.get("cuenta_caja_id"),
            "monto": data.get("monto"),
            "referencia": data.get("referencia"),
            "notas": data.get("notas"),
            "confirmar": bool(data.get("confirmar", True)),
        }
        view.run_api(
            lambda: api.crear_pago(payload),
            on_success=lambda _r: _reload(view),
            loading="Registrando pago…",
            success_toast="Pago registrado",
        )

    FormDialog(
        view,
        "Registrar pago / anticipo",
        [
            ("metodo_pago_id", "Método de pago", "combo"),
            ("cuenta_caja_id", "Cuenta de caja", "combo"),
            ("monto", "Monto", "float"),
            ("referencia", "Referencia", "text"),
            ("notas", "Notas", "textarea"),
            ("confirmar", "Confirmar al crear", "bool"),
        ],
        combos={
            "metodo_pago_id": [(f"{m['id']} — {m['nombre']}", m["id"]) for m in metodos],
            "cuenta_caja_id": [(f"{c['id']} — {c['nombre']}", c["id"]) for c in cuentas],
        },
        initial={"monto": row.get("saldo_pendiente"), "confirmar": True},
        on_submit=submit,
        height=480,
    )


def _cancelar(view: BaseView, api: ApiClient) -> None:
    row = view.table.selected_row()
    if not row:
        view.toast.show("Seleccione un pedido", kind="warning")
        return
    pid = int(row["id"])

    def confirm() -> None:
        view.run_api(
            lambda: api.cancelar_pedido(pid),
            on_success=lambda _r: _reload(view),
            loading="Cancelando pedido…",
            success_toast="Pedido cancelado",
        )

    ConfirmDialog(
        view,
        "Cancelar pedido",
        f"¿Cancelar el pedido {row.get('numero_pedido')}?",
        danger=True,
        confirm_text="Cancelar pedido",
        on_confirm=confirm,
    )
