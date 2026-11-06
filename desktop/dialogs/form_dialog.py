"""Modal de formulario genérico."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import customtkinter as ctk

from desktop.components.buttons import primary_button, secondary_button
from desktop.styles import theme


FieldSpec = tuple[str, str, str]  # key, label, kind: text|int|float|bool|combo|textarea


class FormDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        title: str,
        fields: Sequence[FieldSpec],
        *,
        initial: dict[str, Any] | None = None,
        combos: dict[str, Sequence[tuple[str, Any]]] | None = None,
        on_submit: Callable[[dict[str, Any]], None] | None = None,
        width: int = 480,
        height: int = 520,
    ) -> None:
        super().__init__(master)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.configure(fg_color=theme.BG)
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self._fields = list(fields)
        self._combos = combos or {}
        self._on_submit = on_submit
        self._widgets: dict[str, Any] = {}
        self.result: dict[str, Any] | None = None
        initial = initial or {}

        header = ctk.CTkLabel(self, text=title, font=theme.FONT_SECTION, text_color=theme.TEXT)
        header.pack(anchor="w", padx=20, pady=(18, 8))

        body = ctk.CTkScrollableFrame(self, fg_color=theme.SURFACE, corner_radius=10)
        body.pack(fill="both", expand=True, padx=20, pady=8)

        for key, label, kind in self._fields:
            ctk.CTkLabel(body, text=label, text_color=theme.TEXT_MUTED, font=theme.FONT_SMALL).pack(
                anchor="w", padx=12, pady=(10, 2)
            )
            value = initial.get(key, "")
            if kind == "bool":
                var = ctk.BooleanVar(value=bool(value) if value != "" else True)
                w = ctk.CTkCheckBox(body, text="Activo", variable=var, text_color=theme.TEXT)
                w.pack(anchor="w", padx=12)
                self._widgets[key] = ("bool", var)
            elif kind == "combo":
                options = self._combos.get(key, [])
                labels = [o[0] for o in options] or ["—"]
                w = ctk.CTkComboBox(body, values=labels, width=400)
                # preselect
                if value != "" and value is not None:
                    for lab, val in options:
                        if val == value:
                            w.set(lab)
                            break
                    else:
                        w.set(labels[0])
                else:
                    w.set(labels[0])
                w.pack(anchor="w", padx=12)
                self._widgets[key] = ("combo", w, options)
            elif kind == "textarea":
                w = ctk.CTkTextbox(body, width=400, height=80)
                if value:
                    w.insert("1.0", str(value))
                w.pack(anchor="w", padx=12)
                self._widgets[key] = ("textarea", w)
            else:
                w = ctk.CTkEntry(body, width=400)
                if value is not None and value != "":
                    w.insert(0, str(value))
                w.pack(anchor="w", padx=12)
                self._widgets[key] = (kind, w)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=16)
        secondary_button(actions, "Cancelar", command=self.destroy).pack(side="right", padx=(8, 0))
        primary_button(actions, "Guardar", command=self._submit).pack(side="right")

        self.bind("<Escape>", lambda _e: self.destroy())
        self.after(50, self.lift)

    def _submit(self) -> None:
        data: dict[str, Any] = {}
        for key, _label, kind in self._fields:
            meta = self._widgets[key]
            if meta[0] == "bool":
                data[key] = bool(meta[1].get())
            elif meta[0] == "combo":
                _, widget, options = meta
                label = widget.get()
                matched = next((val for lab, val in options if lab == label), None)
                data[key] = matched
            elif meta[0] == "textarea":
                data[key] = meta[1].get("1.0", "end").strip()
            else:
                raw = meta[1].get().strip()
                if kind == "int":
                    data[key] = int(raw) if raw else None
                elif kind == "float":
                    data[key] = float(raw.replace(",", ".")) if raw else None
                else:
                    data[key] = raw if raw else None
        self.result = data
        if self._on_submit:
            self._on_submit(data)
        self.destroy()
