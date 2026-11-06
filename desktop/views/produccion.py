"""Vistas de producción: órdenes, recetas, seguimiento."""

from __future__ import annotations

import customtkinter as ctk

from desktop.api.client import ApiClient
from desktop.components.buttons import danger_button, primary_button, secondary_button, success_button
from desktop.components.table import DataTable
from desktop.components.toast import ToastHost
from desktop.dialogs.confirm_dialog import ConfirmDialog
from desktop.dialogs.form_dialog import FormDialog
from desktop.styles import theme
from desktop.views.base import BaseView


def build_ordenes_view(master, api: ApiClient, toast: ToastHost) -> BaseView:
    view = BaseView(
        master,
        api,
        toast,
        title="Órdenes de producción",
        subtitle="OP ligadas a pedido (pedido_id obligatorio en V1)",
    )
    primary_button(view.toolbar, "Nueva OP", command=lambda: _nueva_op(view, api)).pack(side="left", padx=(0, 8))
    success_button(view.toolbar, "Iniciar", command=lambda: _accion(view, api, "iniciar")).pack(
        side="left", padx=(0, 8)
    )
    success_button(view.toolbar, "Completar", command=lambda: _accion(view, api, "completar")).pack(
        side="left", padx=(0, 8)
    )
    danger_button(view.toolbar, "Cancelar", command=lambda: _accion(view, api, "cancelar")).pack(
        side="left", padx=(0, 8)
    )
    secondary_button(view.toolbar, "Materiales", command=lambda: _materiales(view, api)).pack(side="left", padx=(0, 8))
    secondary_button(view.toolbar, "Actualizar", command=lambda: _reload_op(view)).pack(side="left")

    view.table = DataTable(
        view.body,
        [
            ("id", "ID", 50),
            ("numero_produccion", "Número", 120),
            ("pedido_id", "Pedido", 80),
            ("estado", "Estado", 120),
            ("fecha_inicio", "Inicio", 140),
            ("fecha_fin", "Fin", 140),
        ],
    )
    view.table.pack(fill="both", expand=True)
    _reload_op(view)
    return view


def _reload_op(view: BaseView) -> None:
    view.run_api(
        view.api.listar_ordenes_produccion,
        on_success=lambda rows: (view.table.set_rows(rows), view.set_status(f"{len(rows)} orden(es)")),
        loading="Cargando órdenes…",
    )


def _nueva_op(view: BaseView, api: ApiClient) -> None:
    try:
        pedidos = api.listar_pedidos()
        bodegas = api.listar_bodegas()
    except Exception as exc:  # noqa: BLE001
        view.toast.show(str(exc), kind="error")
        return

    def submit(data: dict) -> None:
        pedido_id = data.get("pedido_id")

        def work():
            pedido = api.obtener_pedido(pedido_id)
            items = pedido.get("items") or []
            if not items:
                raise ValueError("El pedido no tiene ítems")
            item_pedido_id = data.get("item_pedido_id") or items[0]["id"]
            payload = {
                "pedido_id": pedido_id,
                "numero_produccion": data.get("numero_produccion"),
                "notas": data.get("notas"),
                "bodega_id": data.get("bodega_id"),
                "items": [
                    {
                        "item_pedido_id": item_pedido_id,
                        "cantidad_planificada": data.get("cantidad_planificada") or items[0].get("cantidad"),
                    }
                ],
            }
            return api.crear_orden_produccion(payload)

        view.run_api(
            work,
            on_success=lambda _r: _reload_op(view),
            loading="Creando OP…",
            success_toast="Orden de producción creada",
        )

    FormDialog(
        view,
        "Nueva orden de producción",
        [
            ("pedido_id", "Pedido", "combo"),
            ("bodega_id", "Bodega de consumo", "combo"),
            ("numero_produccion", "Número (opcional)", "text"),
            ("item_pedido_id", "Ítem pedido (id, opcional)", "int"),
            ("cantidad_planificada", "Cantidad planificada", "float"),
            ("notas", "Notas", "textarea"),
        ],
        combos={
            "pedido_id": [
                (f"{p['id']} — {p.get('numero_pedido')} ({p.get('estado')})", p["id"]) for p in pedidos
            ],
            "bodega_id": [(f"{b['id']} — {b['nombre']}", b["id"]) for b in bodegas],
        },
        on_submit=submit,
        height=560,
    )


def _accion(view: BaseView, api: ApiClient, accion: str) -> None:
    row = view.table.selected_row()
    if not row:
        view.toast.show("Seleccione una orden", kind="warning")
        return
    oid = int(row["id"])
    fn = {
        "iniciar": api.iniciar_orden,
        "completar": lambda i: api.completar_orden(i),
        "cancelar": api.cancelar_orden,
    }[accion]

    def confirm() -> None:
        view.run_api(
            lambda: fn(oid),
            on_success=lambda _r: _reload_op(view),
            loading=f"Ejecutando {accion}…",
            success_toast=f"Orden: {accion} OK",
        )

    ConfirmDialog(
        view,
        f"Confirmar {accion}",
        f"¿{accion.capitalize()} la orden {row.get('numero_produccion') or oid}?",
        danger=accion == "cancelar",
        confirm_text=accion.capitalize(),
        on_confirm=confirm,
    )


def _materiales(view: BaseView, api: ApiClient) -> None:
    row = view.table.selected_row()
    if not row:
        view.toast.show("Seleccione una orden", kind="warning")
        return
    oid = int(row["id"])

    def ok(data: dict) -> None:
        mats = data.get("materiales") or []
        if not mats:
            view.toast.show("Sin materiales requeridos (¿hay receta activa?)", kind="warning")
            return
        lines = [
            f"{m.get('nombre_material')}: req {m.get('cantidad_requerida')} / disp {m.get('cantidad_disponible')}"
            f" {'✓' if m.get('suficiente') else '✗'}"
            for m in mats
        ]
        view.toast.show(
            ("OK — " if data.get("todos_suficientes") else "Faltante — ") + " · ".join(lines[:4]),
            kind="success" if data.get("todos_suficientes") else "warning",
            duration_ms=7000,
        )

    view.run_api(lambda: api.materiales_requeridos(oid), on_success=ok, loading="Consultando materiales…")


def build_recetas_view(master, api: ApiClient, toast: ToastHost) -> BaseView:
    view = BaseView(
        master,
        api,
        toast,
        title="Recetas",
        subtitle="Recetas versionadas — activar no sobrescribe historial",
    )
    primary_button(view.toolbar, "Nueva receta", command=lambda: _nueva_receta(view, api)).pack(
        side="left", padx=(0, 8)
    )
    success_button(view.toolbar, "Activar", command=lambda: _activar_receta(view, api)).pack(side="left", padx=(0, 8))
    secondary_button(view.toolbar, "Actualizar", command=lambda: _reload_recetas(view)).pack(side="left")

    view.table = DataTable(
        view.body,
        [
            ("id", "ID", 50),
            ("producto_id", "Producto", 90),
            ("variante_id", "Variante", 90),
            ("nombre", "Nombre", 180),
            ("version", "Versión", 80),
            ("activo", "Activa", 70),
        ],
    )
    view.table.pack(fill="both", expand=True)
    _reload_recetas(view)
    return view


def _reload_recetas(view: BaseView) -> None:
    view.run_api(
        view.api.listar_recetas,
        on_success=lambda rows: (view.table.set_rows(rows), view.set_status(f"{len(rows)} receta(s)")),
        loading="Cargando recetas…",
    )


def _nueva_receta(view: BaseView, api: ApiClient) -> None:
    try:
        productos = api.listar_productos()
        materiales = api.listar_materiales()
    except Exception as exc:  # noqa: BLE001
        view.toast.show(str(exc), kind="error")
        return

    def submit(data: dict) -> None:
        payload = {
            "producto_id": data.get("producto_id"),
            "nombre": data.get("nombre"),
            "activo": False,
            "items": [
                {
                    "material_id": data.get("material_id"),
                    "cantidad": data.get("cantidad"),
                    "porcentaje_desperdicio": data.get("porcentaje_desperdicio") or 0,
                }
            ],
        }
        view.run_api(
            lambda: api.crear_receta(payload),
            on_success=lambda _r: _reload_recetas(view),
            loading="Creando receta…",
            success_toast="Receta creada",
        )

    FormDialog(
        view,
        "Nueva receta",
        [
            ("producto_id", "Producto", "combo"),
            ("nombre", "Nombre", "text"),
            ("material_id", "Material", "combo"),
            ("cantidad", "Cantidad", "float"),
            ("porcentaje_desperdicio", "% desperdicio", "float"),
        ],
        combos={
            "producto_id": [(f"{p['id']} — {p['nombre']}", p["id"]) for p in productos],
            "material_id": [(f"{m['id']} — {m['nombre']}", m["id"]) for m in materiales],
        },
        on_submit=submit,
        height=480,
    )


def _activar_receta(view: BaseView, api: ApiClient) -> None:
    row = view.table.selected_row()
    if not row:
        view.toast.show("Seleccione una receta", kind="warning")
        return
    rid = int(row["id"])
    view.run_api(
        lambda: api.activar_receta(rid),
        on_success=lambda _r: _reload_recetas(view),
        loading="Activando…",
        success_toast="Receta activada",
    )


def build_seguimiento_view(master, api: ApiClient, toast: ToastHost) -> BaseView:
    view = BaseView(
        master,
        api,
        toast,
        title="Seguimiento de producción",
        subtitle="Órdenes en proceso y comparación de costos",
    )
    secondary_button(view.toolbar, "Actualizar", command=lambda: _reload_seg(view)).pack(side="left")

    view.table = DataTable(
        view.body,
        [
            ("id", "ID", 50),
            ("numero_produccion", "Número", 120),
            ("pedido_id", "Pedido", 80),
            ("estado", "Estado", 120),
            ("fecha_inicio", "Inicio", 160),
        ],
    )
    view.table.pack(fill="both", expand=True)

    def _reload_seg(v=view) -> None:
        def work():
            rows = api.listar_ordenes_produccion()
            return [r for r in rows if r.get("estado") in ("PLANIFICADA", "EN_PROCESO")]

        v.run_api(
            work,
            on_success=lambda rows: (v.table.set_rows(rows), v.set_status(f"{len(rows)} en seguimiento")),
            loading="Cargando seguimiento…",
        )

    _reload_seg()
    return view
