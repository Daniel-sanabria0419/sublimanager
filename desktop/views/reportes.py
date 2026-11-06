"""Pantallas de reportes + exportación CSV/PDF (Stage 9)."""

from __future__ import annotations

import os
from pathlib import Path
from tkinter import filedialog
from typing import Any, Callable

import customtkinter as ctk

from desktop.api.client import ApiClient
from desktop.components.buttons import primary_button, secondary_button
from desktop.components.table import DataTable
from desktop.components.toast import ToastHost
from desktop.styles import theme
from desktop.views.base import BaseView

# (clave_api, título, columnas_tabla)
_REPORTES: list[tuple[str, str, list[tuple[str, str, int]]]] = [
    (
        "ventas_diarias",
        "Ventas diarias",
        [("fecha", "Fecha", 120), ("cantidad_pedidos", "Pedidos", 80), ("total_ventas", "Total", 120)],
    ),
    (
        "ventas_mensuales",
        "Ventas mensuales",
        [
            ("periodo", "Periodo", 100),
            ("cantidad_pedidos", "Pedidos", 80),
            ("total_ventas", "Total", 120),
        ],
    ),
    (
        "productos_mas_vendidos",
        "Productos más vendidos",
        [
            ("nombre", "Producto", 180),
            ("tipo_producto", "Tipo", 100),
            ("cantidad_vendida", "Cantidad", 100),
            ("total_ventas", "Total", 120),
        ],
    ),
    (
        "utilidad_por_producto",
        "Utilidad por producto",
        [
            ("nombre", "Producto", 160),
            ("ingreso", "Ingreso", 100),
            ("costo_estimado", "Costo", 100),
            ("utilidad", "Utilidad", 100),
            ("margen_porcentaje", "Margen %", 90),
        ],
    ),
    (
        "rentabilidad_pedidos",
        "Rentabilidad por pedido",
        [
            ("numero_pedido", "Pedido", 120),
            ("ingreso", "Ingreso", 100),
            ("costo_estimado", "Costo", 100),
            ("utilidad", "Utilidad", 100),
            ("margen_porcentaje", "Margen %", 90),
        ],
    ),
    (
        "costos_produccion",
        "Costos de producción",
        [
            ("etapa_costo", "Etapa", 90),
            ("tipo_costo", "Tipo", 120),
            ("categoria", "Categoría", 140),
            ("total", "Total", 100),
        ],
    ),
    (
        "costos_por_categoria",
        "Costos por categoría",
        [("tipo_costo", "Tipo", 160), ("total", "Total", 120)],
    ),
    (
        "compras",
        "Compras",
        [
            ("compra_id", "ID", 60),
            ("proveedor_id", "Proveedor", 90),
            ("estado", "Estado", 120),
            ("total", "Total", 100),
            ("fecha_compra", "Fecha", 160),
        ],
    ),
    (
        "gastos",
        "Gastos",
        [
            ("gasto_id", "ID", 60),
            ("categoria", "Categoría", 140),
            ("descripcion", "Descripción", 180),
            ("monto", "Monto", 100),
            ("estado_pago", "Estado", 100),
        ],
    ),
    (
        "inventario_valorizado",
        "Inventario valorizado",
        [
            ("bodega", "Bodega", 120),
            ("tipo_articulo", "Tipo", 90),
            ("articulo", "Artículo", 180),
            ("cantidad", "Cant.", 80),
            ("valor_total", "Valor", 100),
        ],
    ),
    (
        "consumo_materiales",
        "Consumo de materiales",
        [
            ("nombre", "Material", 160),
            ("cantidad_consumida", "Consumido", 100),
            ("cantidad_desperdicio", "Desperdicio", 100),
            ("costo_total", "Costo", 100),
        ],
    ),
    (
        "desperdicios",
        "Desperdicios",
        [
            ("material", "Material", 160),
            ("cantidad", "Cantidad", 90),
            ("costo_total", "Costo", 100),
            ("consumido_en", "Fecha", 160),
        ],
    ),
    (
        "cuentas_pendientes",
        "Cuentas pendientes (CxC/CxP)",
        [
            ("tipo", "Tipo", 60),
            ("referencia", "Referencia", 140),
            ("total", "Total", 100),
            ("total_pagado", "Pagado", 100),
            ("saldo_pendiente", "Saldo", 100),
        ],
    ),
]

_EXPORTABLES = [
    ("ventas", "Ventas"),
    ("inventario-valorizado", "Inventario valorizado"),
    ("rentabilidad-pedidos", "Rentabilidad pedidos"),
    ("resumen-financiero", "Resumen financiero"),
]


def build_reportes_view(master, api: ApiClient, toast: ToastHost) -> BaseView:
    view = BaseView(
        master,
        api,
        toast,
        title="Reportes",
        subtitle="Consultas reales + exportación CSV/PDF (sin lógica de negocio en la UI)",
    )

    # Selector de reporte
    keys = [k for k, _, _ in _REPORTES]
    titles = {k: t for k, t, _ in _REPORTES}
    view._reporte_key = ctk.StringVar(value=keys[0])
    ctk.CTkLabel(view.toolbar, text="Reporte:", text_color=theme.TEXT_MUTED).pack(
        side="left", padx=(0, 6)
    )
    combo = ctk.CTkComboBox(
        view.toolbar,
        values=[titles[k] for k in keys],
        width=240,
        command=lambda _v: _on_select(view, titles, keys),
    )
    combo.set(titles[keys[0]])
    combo.pack(side="left", padx=(0, 8))
    view._combo = combo
    view._titles = titles
    view._keys = keys

    secondary_button(view.toolbar, "Actualizar", command=lambda: _cargar(view)).pack(
        side="left", padx=(0, 8)
    )

    # Exportaciones clave
    for tipo, label in _EXPORTABLES:
        primary_button(
            view.toolbar,
            f"CSV {label}",
            command=lambda t=tipo: _exportar(view, t, "csv"),
        ).pack(side="left", padx=(0, 4))
        secondary_button(
            view.toolbar,
            f"PDF {label}",
            command=lambda t=tipo: _exportar(view, t, "pdf"),
        ).pack(side="left", padx=(0, 8))

    # Tabla dinámica
    view._tables: dict[str, DataTable] = {}
    view._table_host = ctk.CTkFrame(view.body, fg_color="transparent")
    view._table_host.pack(fill="both", expand=True)
    for key, _title, cols in _REPORTES:
        table = DataTable(view._table_host, cols)
        view._tables[key] = table

    view._current_table: DataTable | None = None
    _mostrar_tabla(view, keys[0])
    _cargar(view)
    return view


def _on_select(view: BaseView, titles: dict[str, str], keys: list[str]) -> None:
    label = view._combo.get()
    for k in keys:
        if titles[k] == label:
            view._reporte_key.set(k)
            _mostrar_tabla(view, k)
            _cargar(view)
            break


def _mostrar_tabla(view: BaseView, key: str) -> None:
    if view._current_table is not None:
        view._current_table.pack_forget()
    table = view._tables[key]
    table.pack(fill="both", expand=True)
    view._current_table = table


def _fetchers(api: ApiClient) -> dict[str, Callable[[], Any]]:
    return {
        "ventas_diarias": api.reporte_ventas_diarias,
        "ventas_mensuales": api.reporte_ventas_mensuales,
        "productos_mas_vendidos": api.reporte_productos_mas_vendidos,
        "utilidad_por_producto": api.reporte_utilidad_por_producto,
        "rentabilidad_pedidos": api.reporte_rentabilidad_pedidos,
        "costos_produccion": api.reporte_costos_produccion,
        "costos_por_categoria": api.reporte_costos_por_categoria,
        "compras": api.reporte_compras,
        "gastos": api.reporte_gastos,
        "inventario_valorizado": api.reporte_inventario_valorizado,
        "consumo_materiales": api.reporte_consumo_materiales,
        "desperdicios": api.reporte_desperdicios,
        "cuentas_pendientes": _fetch_cuentas_pendientes(api),
    }


def _fetch_cuentas_pendientes(api: ApiClient) -> Callable[[], list[dict]]:
    def _inner() -> list[dict]:
        data = api.reporte_cuentas_pendientes()
        rows: list[dict] = []
        for c in data.get("cuentas_por_cobrar") or []:
            rows.append(
                {
                    "tipo": "CxC",
                    "referencia": c.get("numero_pedido"),
                    "total": c.get("total"),
                    "total_pagado": c.get("total_pagado"),
                    "saldo_pendiente": c.get("saldo_pendiente"),
                }
            )
        for c in data.get("cuentas_por_pagar") or []:
            rows.append(
                {
                    "tipo": "CxP",
                    "referencia": c.get("numero_factura") or f"Compra {c.get('compra_id')}",
                    "total": c.get("total"),
                    "total_pagado": c.get("total_pagado"),
                    "saldo_pendiente": c.get("saldo_pendiente"),
                }
            )
        return rows

    return _inner


def _cargar(view: BaseView) -> None:
    key = view._reporte_key.get()
    fetcher = _fetchers(view.api)[key]

    def ok(rows: list) -> None:
        view._tables[key].set_rows(rows or [])
        view.set_status(f"{len(rows or [])} fila(s) — {view._titles[key]}")

    view.run_api(fetcher, on_success=ok, loading=f"Cargando {view._titles[key]}…")


def _exportar(view: BaseView, tipo: str, formato: str) -> None:
    ext = "csv" if formato == "csv" else "pdf"
    default = f"reporte-{tipo}.{ext}"
    path = filedialog.asksaveasfilename(
        parent=view.winfo_toplevel(),
        title=f"Guardar {tipo} ({formato.upper()})",
        defaultextension=f".{ext}",
        initialfile=default,
        filetypes=[(formato.upper(), f"*.{ext}"), ("Todos", "*.*")],
    )
    if not path:
        return

    def work():
        content, filename = view.api.exportar_reporte(tipo, formato=formato)
        dest = Path(path)
        dest.write_bytes(content)
        return str(dest), filename

    def ok(result) -> None:
        dest, _name = result
        view.set_status(f"Exportado: {dest}")
        view.toast.show(f"Archivo guardado: {os.path.basename(dest)}", kind="success")

    view.run_api(work, on_success=ok, loading=f"Exportando {tipo}…")
