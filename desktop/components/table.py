"""Tabla reutilizable basada en ttk.Treeview (Tkinter solo donde CustomTkinter no alcanza)."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import customtkinter as ctk
from tkinter import ttk

from desktop.styles import theme


class DataTable(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        columns: Sequence[tuple[str, str, int]],
        *,
        on_select: Callable[[dict[str, Any] | None], None] | None = None,
        height: int = 280,
        **kwargs,
    ) -> None:
        """
        columns: lista de (key, encabezado, ancho_px)
        """
        super().__init__(master, fg_color=theme.SURFACE, corner_radius=8, **kwargs)
        self._columns = list(columns)
        self._on_select = on_select
        self._rows: list[dict[str, Any]] = []
        self._iid_map: dict[str, dict[str, Any]] = {}

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "Subli.Treeview",
            background=theme.SURFACE,
            foreground=theme.TEXT,
            fieldbackground=theme.SURFACE,
            borderwidth=0,
            rowheight=28,
            font=theme.FONT_BODY,
        )
        style.configure(
            "Subli.Treeview.Heading",
            background=theme.BG,
            foreground=theme.TEXT_MUTED,
            font=theme.FONT_SMALL,
            relief="flat",
        )
        style.map("Subli.Treeview", background=[("selected", "#DBEAFE")], foreground=[("selected", theme.TEXT)])

        keys = [c[0] for c in self._columns]
        self._tree = ttk.Treeview(
            self,
            columns=keys,
            show="headings",
            style="Subli.Treeview",
            height=max(8, height // 28),
            selectmode="browse",
        )
        for key, heading, width in self._columns:
            self._tree.heading(key, text=heading)
            self._tree.column(key, width=width, anchor="w", stretch=True)

        vsb = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=1)
        vsb.pack(side="right", fill="y", pady=1)
        self._tree.bind("<<TreeviewSelect>>", self._handle_select)

        self._empty = ctk.CTkLabel(
            self, text="Sin registros", text_color=theme.TEXT_MUTED, font=theme.FONT_BODY
        )

    def set_rows(self, rows: Sequence[dict[str, Any]]) -> None:
        self._tree.delete(*self._tree.get_children())
        self._rows = list(rows)
        self._iid_map.clear()
        for idx, row in enumerate(self._rows):
            values = [self._fmt(row.get(key)) for key, _, _ in self._columns]
            iid = str(idx)
            self._tree.insert("", "end", iid=iid, values=values)
            self._iid_map[iid] = row
        if not self._rows:
            self._empty.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self._empty.place_forget()

    def selected_row(self) -> dict[str, Any] | None:
        sel = self._tree.selection()
        if not sel:
            return None
        return self._iid_map.get(sel[0])

    def _handle_select(self, _event=None) -> None:
        if self._on_select:
            self._on_select(self.selected_row())

    @staticmethod
    def _fmt(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "Sí" if value else "No"
        return str(value)
