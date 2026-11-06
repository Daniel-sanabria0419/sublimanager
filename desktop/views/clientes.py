"""Vista Clientes."""

from __future__ import annotations

from desktop.api.client import ApiClient
from desktop.components.toast import ToastHost
from desktop.views.base import CrudListView


def build_clientes_view(master, api: ApiClient, toast: ToastHost) -> CrudListView:
    return CrudListView(
        master,
        api,
        toast,
        title="Clientes",
        subtitle="Gestión de clientes (CRUD vía API)",
        columns=[
            ("id", "ID", 60),
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
            ("notas", "Notas", "textarea"),
            ("activo", "Activo", "bool"),
        ],
        list_fn=api.listar_clientes,
        create_fn=api.crear_cliente,
        update_fn=api.actualizar_cliente,
        delete_fn=api.eliminar_cliente,
    )
