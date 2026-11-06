"""Vistas de inventario: insumos, existencias, movimientos."""

from __future__ import annotations

from desktop.api.client import ApiClient
from desktop.components.buttons import primary_button, secondary_button, success_button
from desktop.components.toast import ToastHost
from desktop.dialogs.form_dialog import FormDialog
from desktop.views.base import BaseView, CrudListView


def build_insumos_view(master, api: ApiClient, toast: ToastHost) -> CrudListView:
    def combos():
        cats = api.listar_categorias_material()
        unidades = api.listar_unidades()
        bodegas = api.listar_bodegas()
        return {
            "categoria_id": [(f"{c['id']} — {c['nombre']}", c["id"]) for c in cats] or [("—", None)],
            "unidad_id": [(f"{u['id']} — {u['abreviatura']}", u["id"]) for u in unidades] or [("—", None)],
            "bodega_id": [(f"{b['id']} — {b['nombre']}", b["id"]) for b in bodegas] or [("—", None)],
        }

    def prepare(data: dict, is_update: bool) -> dict:
        payload = {
            "nombre": data.get("nombre"),
            "descripcion": data.get("descripcion"),
            "stock_minimo": data.get("stock_minimo") or 0,
            "activo": bool(data.get("activo", True)),
            "categoria_id": data.get("categoria_id"),
            "unidad_id": data.get("unidad_id"),
        }
        if not is_update and data.get("stock_inicial") is not None:
            payload["stock_inicial"] = data["stock_inicial"]
            payload["bodega_id"] = data.get("bodega_id")
            payload["costo_unitario_inicial"] = data.get("costo_unitario_inicial") or 0
        return payload

    return CrudListView(
        master,
        api,
        toast,
        title="Insumos",
        subtitle="Materiales e insumos de sublimación",
        columns=[
            ("id", "ID", 50),
            ("nombre", "Nombre", 200),
            ("stock_minimo", "Stock mín.", 90),
            ("costo_promedio", "Costo prom.", 100),
            ("activo", "Activo", 70),
        ],
        fields=[
            ("categoria_id", "Categoría", "combo"),
            ("unidad_id", "Unidad", "combo"),
            ("nombre", "Nombre", "text"),
            ("descripcion", "Descripción", "textarea"),
            ("stock_minimo", "Stock mínimo", "float"),
            ("stock_inicial", "Stock inicial (alta)", "float"),
            ("bodega_id", "Bodega (stock inicial)", "combo"),
            ("costo_unitario_inicial", "Costo unit. inicial", "float"),
            ("activo", "Activo", "bool"),
        ],
        list_fn=api.listar_materiales,
        create_fn=api.crear_material,
        update_fn=api.actualizar_material,
        combos_provider=combos,
        prepare_payload=prepare,
    )


def build_productos_terminados_view(master, api: ApiClient, toast: ToastHost) -> CrudListView:
    def transform(row: dict) -> dict:
        return {
            **row,
            "tipo": "variante" if row.get("variante_producto_id") else "material",
            "ref_id": row.get("variante_producto_id") or row.get("material_id"),
        }

    return CrudListView(
        master,
        api,
        toast,
        title="Productos terminados",
        subtitle="Existencias (materiales y variantes) por bodega",
        columns=[
            ("id", "ID", 50),
            ("bodega_id", "Bodega", 80),
            ("material_id", "Material", 90),
            ("variante_producto_id", "Variante", 90),
            ("cantidad", "Cantidad", 100),
        ],
        fields=[],
        list_fn=api.listar_existencias,
        transform_row=transform,
    )


def build_movimientos_view(master, api: ApiClient, toast: ToastHost) -> BaseView:
    view = BaseView(
        master,
        api,
        toast,
        title="Movimientos de inventario",
        subtitle="Entradas, salidas, ajustes y transferencias",
    )
    from desktop.components.table import DataTable

    primary_button(view.toolbar, "Nuevo movimiento", command=lambda: _nuevo_movimiento(view, api)).pack(
        side="left", padx=(0, 8)
    )
    success_button(view.toolbar, "Confirmar", command=lambda: _confirmar(view, api)).pack(side="left", padx=(0, 8))
    secondary_button(view.toolbar, "Actualizar", command=lambda: _reload(view)).pack(side="left")

    view.table = DataTable(
        view.body,
        [
            ("id", "ID", 50),
            ("tipo_movimiento", "Tipo", 140),
            ("estado", "Estado", 100),
            ("bodega_id", "Bodega", 80),
            ("fecha_movimiento", "Fecha", 160),
            ("notas", "Notas", 200),
        ],
    )
    view.table.pack(fill="both", expand=True)
    _reload(view)
    return view


def _reload(view: BaseView) -> None:
    view.run_api(
        view.api.listar_movimientos,
        on_success=lambda rows: (view.table.set_rows(rows), view.set_status(f"{len(rows)} movimiento(s)")),
        loading="Cargando movimientos…",
    )


def _nuevo_movimiento(view: BaseView, api: ApiClient) -> None:
    try:
        bodegas = api.listar_bodegas()
        materiales = api.listar_materiales()
    except Exception as exc:  # noqa: BLE001
        view.toast.show(str(exc), kind="error")
        return

    tipos = [
        ("ENTRADA", "ENTRADA"),
        ("SALIDA", "SALIDA"),
        ("AJUSTE", "AJUSTE"),
    ]

    def submit(data: dict) -> None:
        payload = {
            "tipo_movimiento": data.get("tipo_movimiento"),
            "bodega_id": data.get("bodega_id"),
            "notas": data.get("notas"),
            "confirmar": bool(data.get("confirmar", True)),
            "items": [
                {
                    "material_id": data.get("material_id"),
                    "cantidad": data.get("cantidad"),
                    "costo_unitario": data.get("costo_unitario"),
                }
            ],
        }
        view.run_api(
            lambda: api.crear_movimiento(payload),
            on_success=lambda _r: _reload(view),
            loading="Creando movimiento…",
            success_toast="Movimiento creado",
        )

    FormDialog(
        view,
        "Nuevo movimiento",
        [
            ("tipo_movimiento", "Tipo", "combo"),
            ("bodega_id", "Bodega", "combo"),
            ("material_id", "Material", "combo"),
            ("cantidad", "Cantidad", "float"),
            ("costo_unitario", "Costo unitario", "float"),
            ("notas", "Notas", "textarea"),
            ("confirmar", "Confirmar al crear", "bool"),
        ],
        combos={
            "tipo_movimiento": tipos,
            "bodega_id": [(f"{b['id']} — {b['nombre']}", b["id"]) for b in bodegas],
            "material_id": [(f"{m['id']} — {m['nombre']}", m["id"]) for m in materiales],
        },
        on_submit=submit,
        height=560,
    )


def _confirmar(view: BaseView, api: ApiClient) -> None:
    row = view.table.selected_row()
    if not row:
        view.toast.show("Seleccione un movimiento", kind="warning")
        return
    mid = int(row["id"])
    view.run_api(
        lambda: api.confirmar_movimiento(mid),
        on_success=lambda _r: _reload(view),
        loading="Confirmando…",
        success_toast="Movimiento confirmado",
    )
