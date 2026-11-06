"""Vistas financieras: resumen, ingresos, gastos, CxC, CxP, caja."""

from __future__ import annotations

import customtkinter as ctk

from desktop.api.client import ApiClient
from desktop.components.buttons import primary_button, secondary_button, success_button
from desktop.components.cards import KpiCard
from desktop.components.table import DataTable
from desktop.components.toast import ToastHost
from desktop.dialogs.form_dialog import FormDialog
from desktop.styles import theme
from desktop.views.base import BaseView


def _money(value) -> str:
    try:
        return f"$ {float(value):,.2f}"
    except (TypeError, ValueError):
        return "—"


def build_resumen_view(master, api: ApiClient, toast: ToastHost) -> BaseView:
    view = BaseView(
        master,
        api,
        toast,
        title="Resumen financiero",
        subtitle="Agregados oficiales de /api/v1/finanzas/resumen",
    )
    secondary_button(view.toolbar, "Actualizar", command=lambda: _load_resumen(view)).pack(side="left")

    grid = ctk.CTkFrame(view.body, fg_color="transparent")
    grid.pack(fill="x")
    for i in range(3):
        grid.grid_columnconfigure(i, weight=1)

    view.cards = {
        "ventas": KpiCard(grid, "Ventas reconocidas"),
        "cobrado": KpiCard(grid, "Dinero recibido", accent=theme.SUCCESS),
        "cxc": KpiCard(grid, "CxC", accent=theme.WARNING),
        "costos": KpiCard(grid, "Costos producción"),
        "gastos": KpiCard(grid, "Gastos operativos", accent=theme.ERROR),
        "utilidad": KpiCard(grid, "Utilidad operativa", accent=theme.SUCCESS),
    }
    for i, card in enumerate(view.cards.values()):
        card.grid(row=i // 3, column=i % 3, sticky="ew", padx=(0 if i % 3 == 0 else 8, 0), pady=(0, 8))

    _load_resumen(view)
    return view


def _load_resumen(view: BaseView) -> None:
    def ok(data: dict) -> None:
        view.cards["ventas"].set_value(_money(data.get("ventas_reconocidas")))
        view.cards["cobrado"].set_value(_money(data.get("dinero_recibido")))
        view.cards["cxc"].set_value(_money(data.get("cuentas_por_cobrar")))
        view.cards["costos"].set_value(_money(data.get("costos_produccion")))
        view.cards["gastos"].set_value(_money(data.get("gastos_operativos")))
        view.cards["utilidad"].set_value(_money(data.get("utilidad_operativa")))
        view.set_status("Resumen actualizado")

    view.run_api(view.api.resumen_financiero, on_success=ok, loading="Cargando resumen…")


def build_ingresos_view(master, api: ApiClient, toast: ToastHost) -> BaseView:
    view = BaseView(master, api, toast, title="Ingresos", subtitle="Pagos de clientes (anticipos y saldos)")
    primary_button(view.toolbar, "Nuevo pago", command=lambda: _nuevo_pago(view, api)).pack(side="left", padx=(0, 8))
    success_button(view.toolbar, "Confirmar", command=lambda: _confirmar_pago(view, api)).pack(
        side="left", padx=(0, 8)
    )
    secondary_button(view.toolbar, "Actualizar", command=lambda: _reload_pagos(view)).pack(side="left")
    view.table = DataTable(
        view.body,
        [
            ("id", "ID", 50),
            ("pedido_id", "Pedido", 80),
            ("monto", "Monto", 100),
            ("estado", "Estado", 100),
            ("fecha_pago", "Fecha", 160),
            ("referencia", "Referencia", 140),
        ],
    )
    view.table.pack(fill="both", expand=True)
    _reload_pagos(view)
    return view


def _reload_pagos(view: BaseView) -> None:
    view.run_api(
        view.api.listar_pagos,
        on_success=lambda rows: (view.table.set_rows(rows), view.set_status(f"{len(rows)} pago(s)")),
        loading="Cargando ingresos…",
    )


def _nuevo_pago(view: BaseView, api: ApiClient) -> None:
    try:
        pedidos = api.listar_pedidos()
        metodos = api.listar_metodos_pago()
        cuentas = api.listar_cuentas_caja()
    except Exception as exc:  # noqa: BLE001
        view.toast.show(str(exc), kind="error")
        return

    def submit(data: dict) -> None:
        payload = {
            "pedido_id": data.get("pedido_id"),
            "metodo_pago_id": data.get("metodo_pago_id"),
            "cuenta_caja_id": data.get("cuenta_caja_id"),
            "monto": data.get("monto"),
            "referencia": data.get("referencia"),
            "confirmar": bool(data.get("confirmar", True)),
        }
        view.run_api(
            lambda: api.crear_pago(payload),
            on_success=lambda _r: _reload_pagos(view),
            loading="Registrando…",
            success_toast="Pago creado",
        )

    FormDialog(
        view,
        "Nuevo ingreso",
        [
            ("pedido_id", "Pedido", "combo"),
            ("metodo_pago_id", "Método", "combo"),
            ("cuenta_caja_id", "Cuenta", "combo"),
            ("monto", "Monto", "float"),
            ("referencia", "Referencia", "text"),
            ("confirmar", "Confirmar", "bool"),
        ],
        combos={
            "pedido_id": [(f"{p['id']} — {p.get('numero_pedido')}", p["id"]) for p in pedidos],
            "metodo_pago_id": [(f"{m['id']} — {m['nombre']}", m["id"]) for m in metodos],
            "cuenta_caja_id": [(f"{c['id']} — {c['nombre']}", c["id"]) for c in cuentas],
        },
        on_submit=submit,
        height=500,
    )


def _confirmar_pago(view: BaseView, api: ApiClient) -> None:
    row = view.table.selected_row()
    if not row:
        view.toast.show("Seleccione un pago", kind="warning")
        return
    view.run_api(
        lambda: api.confirmar_pago(int(row["id"])),
        on_success=lambda _r: _reload_pagos(view),
        loading="Confirmando…",
        success_toast="Pago confirmado",
    )


def build_gastos_view(master, api: ApiClient, toast: ToastHost) -> BaseView:
    view = BaseView(master, api, toast, title="Gastos", subtitle="Gastos operativos (no compras de inventario)")
    primary_button(view.toolbar, "Nuevo gasto", command=lambda: _nuevo_gasto(view, api)).pack(side="left", padx=(0, 8))
    success_button(view.toolbar, "Pagar", command=lambda: _pagar_gasto(view, api)).pack(side="left", padx=(0, 8))
    secondary_button(view.toolbar, "Actualizar", command=lambda: _reload_gastos(view)).pack(side="left")
    view.table = DataTable(
        view.body,
        [
            ("id", "ID", 50),
            ("descripcion", "Descripción", 200),
            ("monto", "Monto", 90),
            ("estado_pago", "Estado", 100),
            ("total_pagado", "Pagado", 90),
            ("saldo_pendiente", "Saldo", 90),
        ],
    )
    view.table.pack(fill="both", expand=True)
    _reload_gastos(view)
    return view


def _reload_gastos(view: BaseView) -> None:
    view.run_api(
        view.api.listar_gastos,
        on_success=lambda rows: (view.table.set_rows(rows), view.set_status(f"{len(rows)} gasto(s)")),
        loading="Cargando gastos…",
    )


def _nuevo_gasto(view: BaseView, api: ApiClient) -> None:
    try:
        cats = api.listar_categorias_gasto()
    except Exception as exc:  # noqa: BLE001
        view.toast.show(str(exc), kind="error")
        return

    def submit(data: dict) -> None:
        payload = {
            "categoria_id": data.get("categoria_id"),
            "descripcion": data.get("descripcion"),
            "monto": data.get("monto"),
            "notas": data.get("notas"),
        }
        view.run_api(
            lambda: api.crear_gasto(payload),
            on_success=lambda _r: _reload_gastos(view),
            loading="Creando gasto…",
            success_toast="Gasto creado",
        )

    FormDialog(
        view,
        "Nuevo gasto",
        [
            ("categoria_id", "Categoría", "combo"),
            ("descripcion", "Descripción", "text"),
            ("monto", "Monto", "float"),
            ("notas", "Notas", "textarea"),
        ],
        combos={"categoria_id": [(f"{c['id']} — {c['nombre']}", c["id"]) for c in cats]},
        on_submit=submit,
        height=420,
    )


def _pagar_gasto(view: BaseView, api: ApiClient) -> None:
    row = view.table.selected_row()
    if not row:
        view.toast.show("Seleccione un gasto", kind="warning")
        return
    try:
        metodos = api.listar_metodos_pago()
        cuentas = api.listar_cuentas_caja()
    except Exception as exc:  # noqa: BLE001
        view.toast.show(str(exc), kind="error")
        return
    gid = int(row["id"])

    def submit(data: dict) -> None:
        payload = {
            "gasto_id": gid,
            "metodo_pago_id": data.get("metodo_pago_id"),
            "cuenta_caja_id": data.get("cuenta_caja_id"),
            "monto": data.get("monto"),
            "confirmar": True,
        }
        view.run_api(
            lambda: api.crear_pago_gasto(payload),
            on_success=lambda _r: _reload_gastos(view),
            loading="Registrando pago…",
            success_toast="Pago de gasto registrado",
        )

    FormDialog(
        view,
        "Pagar gasto",
        [
            ("metodo_pago_id", "Método", "combo"),
            ("cuenta_caja_id", "Cuenta", "combo"),
            ("monto", "Monto", "float"),
        ],
        combos={
            "metodo_pago_id": [(f"{m['id']} — {m['nombre']}", m["id"]) for m in metodos],
            "cuenta_caja_id": [(f"{c['id']} — {c['nombre']}", c["id"]) for c in cuentas],
        },
        initial={"monto": row.get("saldo_pendiente")},
        on_submit=submit,
        height=360,
    )


def build_cxc_view(master, api: ApiClient, toast: ToastHost) -> BaseView:
    view = BaseView(master, api, toast, title="Cuentas por cobrar", subtitle="Pedidos con saldo pendiente")
    secondary_button(view.toolbar, "Actualizar", command=lambda: _load_list(view, api.cuentas_por_cobrar)).pack(
        side="left"
    )
    view.table = DataTable(
        view.body,
        [
            ("pedido_id", "Pedido", 80),
            ("numero_pedido", "Número", 120),
            ("cliente_id", "Cliente", 80),
            ("estado", "Estado", 120),
            ("total", "Total", 90),
            ("total_pagado", "Pagado", 90),
            ("saldo_pendiente", "Saldo", 90),
        ],
    )
    view.table.pack(fill="both", expand=True)
    _load_list(view, api.cuentas_por_cobrar)
    return view


def build_cxp_view(master, api: ApiClient, toast: ToastHost) -> BaseView:
    view = BaseView(master, api, toast, title="Cuentas por pagar", subtitle="Compras con saldo pendiente")
    secondary_button(view.toolbar, "Actualizar", command=lambda: _load_list(view, api.cuentas_por_pagar)).pack(
        side="left"
    )
    view.table = DataTable(
        view.body,
        [
            ("compra_id", "Compra", 80),
            ("proveedor_id", "Proveedor", 90),
            ("numero_factura", "Factura", 120),
            ("estado", "Estado", 100),
            ("total", "Total", 90),
            ("total_pagado", "Pagado", 90),
            ("saldo_pendiente", "Saldo", 90),
        ],
    )
    view.table.pack(fill="both", expand=True)
    _load_list(view, api.cuentas_por_pagar)
    return view


def build_caja_view(master, api: ApiClient, toast: ToastHost) -> BaseView:
    view = BaseView(master, api, toast, title="Caja", subtitle="Saldos por cuenta y movimientos")
    secondary_button(view.toolbar, "Actualizar", command=lambda: _reload_caja(view)).pack(side="left")

    saldos_frame = ctk.CTkFrame(view.body, fg_color="transparent")
    saldos_frame.pack(fill="x", pady=(0, 8))
    view.saldos_label = ctk.CTkLabel(
        saldos_frame, text="", font=theme.FONT_BODY, text_color=theme.TEXT, anchor="w", justify="left"
    )
    view.saldos_label.pack(fill="x")

    view.table = DataTable(
        view.body,
        [
            ("id", "ID", 50),
            ("cuenta_caja_id", "Cuenta", 80),
            ("tipo_movimiento", "Tipo", 100),
            ("monto", "Monto", 100),
            ("fecha_movimiento", "Fecha", 160),
            ("descripcion", "Descripción", 200),
        ],
    )
    view.table.pack(fill="both", expand=True)
    _reload_caja(view)
    return view


def _reload_caja(view: BaseView) -> None:
    def work():
        saldos = view.api.saldos_caja()
        movs = view.api.listar_movimientos_caja()
        return saldos, movs

    def ok(result) -> None:
        saldos, movs = result
        texto = " · ".join(f"{s.get('nombre')}: {_money(s.get('saldo'))}" for s in saldos) or "Sin cuentas"
        view.saldos_label.configure(text=texto)
        view.table.set_rows(movs)
        view.set_status(f"{len(movs)} movimiento(s) de caja")

    view.run_api(work, on_success=ok, loading="Cargando caja…")


def _load_list(view: BaseView, fn) -> None:
    view.run_api(
        fn,
        on_success=lambda rows: (view.table.set_rows(rows), view.set_status(f"{len(rows)} registro(s)")),
        loading="Cargando…",
    )
