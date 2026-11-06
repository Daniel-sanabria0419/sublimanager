"""Vista base con toolbar, tabla, estados de carga/error."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import customtkinter as ctk

from desktop.api.client import ApiClient, ApiError
from desktop.components.buttons import danger_button, primary_button, secondary_button
from desktop.components.table import DataTable
from desktop.components.toast import ToastHost
from desktop.dialogs.confirm_dialog import ConfirmDialog
from desktop.dialogs.form_dialog import FieldSpec, FormDialog
from desktop.styles import theme
from desktop.utils.async_ui import run_async


class BaseView(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        api: ApiClient,
        toast: ToastHost,
        *,
        title: str,
        subtitle: str = "",
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color=theme.BG, **kwargs)
        self.api = api
        self.toast = toast
        self._busy = False

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(header, text=title, font=theme.FONT_TITLE, text_color=theme.TEXT).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(header, text=subtitle, font=theme.FONT_BODY, text_color=theme.TEXT_MUTED).pack(
                anchor="w", pady=(2, 0)
            )

        self.toolbar = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar.pack(fill="x", padx=20, pady=(0, 8))

        self.status = ctk.CTkLabel(self, text="", font=theme.FONT_SMALL, text_color=theme.TEXT_MUTED, anchor="w")
        self.status.pack(fill="x", padx=20)

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=20, pady=(4, 16))

    def set_status(self, text: str, *, error: bool = False) -> None:
        self.status.configure(text=text, text_color=theme.ERROR if error else theme.TEXT_MUTED)

    def set_busy(self, busy: bool, message: str = "Cargando…") -> None:
        self._busy = busy
        if busy:
            self.set_status(message)
        elif not self.status.cget("text").startswith("Error"):
            self.set_status("")

    def run_api(
        self,
        work: Callable[[], Any],
        *,
        on_success: Callable[[Any], None] | None = None,
        loading: str = "Cargando…",
        success_toast: str | None = None,
    ) -> None:
        if self._busy:
            return
        self.set_busy(True, loading)

        def _ok(result: Any) -> None:
            if success_toast:
                self.toast.show(success_toast, kind="success")
            if on_success:
                on_success(result)

        def _err(exc: Exception) -> None:
            msg = exc.message if isinstance(exc, ApiError) else str(exc)
            self.set_status(f"Error: {msg}", error=True)
            self.toast.show(msg, kind="error")

        run_async(
            self,
            work,
            on_success=_ok,
            on_error=_err,
            on_finally=lambda: self.set_busy(False, ""),
        )


class CrudListView(BaseView):
    """Lista + alta/edición genérica contra el API client."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        api: ApiClient,
        toast: ToastHost,
        *,
        title: str,
        subtitle: str,
        columns: Sequence[tuple[str, str, int]],
        fields: Sequence[FieldSpec],
        list_fn: Callable[[], list[dict]],
        create_fn: Callable[[dict], dict] | None = None,
        update_fn: Callable[[int, dict], dict] | None = None,
        delete_fn: Callable[[int], Any] | None = None,
        id_key: str = "id",
        combos_provider: Callable[[], dict[str, list[tuple[str, Any]]]] | None = None,
        transform_row: Callable[[dict], dict] | None = None,
        prepare_payload: Callable[[dict, bool], dict] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, api, toast, title=title, subtitle=subtitle, **kwargs)
        self._list_fn = list_fn
        self._create_fn = create_fn
        self._update_fn = update_fn
        self._delete_fn = delete_fn
        self._fields = list(fields)
        self._id_key = id_key
        self._combos_provider = combos_provider
        self._transform_row = transform_row
        self._prepare_payload = prepare_payload

        if create_fn:
            primary_button(self.toolbar, "Nuevo", command=self._on_create).pack(side="left", padx=(0, 8))
        if update_fn:
            secondary_button(self.toolbar, "Editar", command=self._on_edit).pack(side="left", padx=(0, 8))
        if delete_fn:
            danger_button(self.toolbar, "Eliminar", command=self._on_delete).pack(side="left", padx=(0, 8))
        secondary_button(self.toolbar, "Actualizar", command=self.reload).pack(side="left")

        self.table = DataTable(self.body, columns)
        self.table.pack(fill="both", expand=True)
        self.reload()

    def reload(self) -> None:
        def _ok(rows: list[dict]) -> None:
            mapped = [self._transform_row(r) if self._transform_row else r for r in rows]
            self.table.set_rows(mapped)
            self.set_status(f"{len(mapped)} registro(s)")

        self.run_api(self._list_fn, on_success=_ok, loading="Cargando listado…")

    def _safe_combos(self) -> dict[str, list[tuple[str, Any]]]:
        if not self._combos_provider:
            return {}
        try:
            return self._combos_provider()
        except Exception as exc:  # noqa: BLE001
            msg = exc.message if isinstance(exc, ApiError) else str(exc)
            self.toast.show(f"No se pudieron cargar opciones: {msg}", kind="error")
            return {}

    def _on_create(self) -> None:
        combos = self._safe_combos()

        def submit(data: dict) -> None:
            payload = self._prepare_payload(data, False) if self._prepare_payload else data
            self.run_api(
                lambda: self._create_fn(payload),  # type: ignore[misc]
                on_success=lambda _r: self.reload(),
                loading="Guardando…",
                success_toast="Registro creado",
            )

        FormDialog(self, "Nuevo", self._fields, combos=combos, on_submit=submit)

    def _on_edit(self) -> None:
        row = self.table.selected_row()
        if not row:
            self.toast.show("Seleccione un registro", kind="warning")
            return
        if not self._update_fn:
            return
        combos = self._safe_combos()
        entity_id = int(row[self._id_key])

        def submit(data: dict) -> None:
            payload = self._prepare_payload(data, True) if self._prepare_payload else data
            self.run_api(
                lambda: self._update_fn(entity_id, payload),  # type: ignore[misc]
                on_success=lambda _r: self.reload(),
                loading="Guardando…",
                success_toast="Registro actualizado",
            )

        FormDialog(self, "Editar", self._fields, initial=row, combos=combos, on_submit=submit)

    def _on_delete(self) -> None:
        row = self.table.selected_row()
        if not row:
            self.toast.show("Seleccione un registro", kind="warning")
            return
        if not self._delete_fn:
            return
        entity_id = int(row[self._id_key])

        def confirm() -> None:
            self.run_api(
                lambda: self._delete_fn(entity_id),  # type: ignore[misc]
                on_success=lambda _r: self.reload(),
                loading="Eliminando…",
                success_toast="Registro eliminado / desactivado",
            )

        ConfirmDialog(
            self,
            "Confirmar eliminación",
            "¿Desea eliminar o desactivar este registro?",
            danger=True,
            confirm_text="Eliminar",
            on_confirm=confirm,
        )
