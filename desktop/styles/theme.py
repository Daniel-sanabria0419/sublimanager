"""Paleta y tipografía SubliManager (master prompt §6)."""

from __future__ import annotations

# Colores oficiales
BG = "#F5F7FA"
SIDEBAR = "#172033"
SURFACE = "#FFFFFF"
PRIMARY = "#2563EB"
SUCCESS = "#16A34A"
WARNING = "#F59E0B"
ERROR = "#DC2626"
TEXT = "#1E293B"
TEXT_MUTED = "#64748B"
SIDEBAR_HOVER = "#1F2A44"
SIDEBAR_ACTIVE = "#2563EB"
BORDER = "#E2E8F0"

FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 20, "bold")
FONT_SECTION = (FONT_FAMILY, 14, "bold")
FONT_BODY = (FONT_FAMILY, 13)
FONT_SMALL = (FONT_FAMILY, 11)
FONT_SIDEBAR = (FONT_FAMILY, 12)
FONT_SIDEBAR_SECTION = (FONT_FAMILY, 10, "bold")

# Menú lateral (español) — estructura del master prompt §6
MENU_SECTIONS: list[tuple[str, list[tuple[str, str]]]] = [
    ("GENERAL", [("dashboard", "Dashboard")]),
    (
        "VENTAS",
        [
            ("pedidos", "Pedidos"),
            ("clientes", "Clientes"),
            ("productos", "Productos"),
        ],
    ),
    (
        "PRODUCCIÓN",
        [
            ("ordenes_produccion", "Órdenes de producción"),
            ("recetas", "Recetas"),
            ("seguimiento", "Seguimiento"),
        ],
    ),
    (
        "INVENTARIO",
        [
            ("insumos", "Insumos"),
            ("productos_terminados", "Productos terminados"),
            ("movimientos", "Movimientos"),
            ("compras", "Compras"),
            ("proveedores", "Proveedores"),
        ],
    ),
    (
        "FINANZAS",
        [
            ("finanzas_resumen", "Resumen"),
            ("ingresos", "Ingresos"),
            ("gastos", "Gastos"),
            ("cuentas_por_cobrar", "Cuentas por cobrar"),
            ("cuentas_por_pagar", "Cuentas por pagar"),
            ("caja", "Caja"),
        ],
    ),
    (
        "REPORTES",
        [
            ("reportes", "Reportes (próximamente)"),
        ],
    ),
    (
        "CONFIGURACIÓN",
        [
            ("datos_negocio", "Datos del negocio"),
            ("categorias", "Categorías"),
            ("unidades", "Unidades"),
            ("metodos_pago", "Métodos de pago"),
            ("cuentas", "Cuentas"),
        ],
    ),
]
