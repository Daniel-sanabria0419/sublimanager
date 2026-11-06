"""Modal de confirmación."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from desktop.components.buttons import danger_button, primary_button, secondary_button
from desktop.styles import theme


class ConfirmDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        title: str,
        message: str,
        *,
        confirm_text: str = "Confirmar",
        danger: bool = False,
        on_confirm: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master)
        self.title(title)
        self.geometry("420x200")
        self.configure(fg_color=theme.BG)
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self.confirmed = False

        ctk.CTkLabel(self, text=title, font=theme.FONT_SECTION, text_color=theme.TEXT).pack(
            anchor="w", padx=20, pady=(20, 8)
        )
        ctk.CTkLabel(
            self, text=message, font=theme.FONT_BODY, text_color=theme.TEXT_MUTED, wraplength=360, justify="left"
        ).pack(anchor="w", padx=20, pady=4)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=20)

        def _ok() -> None:
            self.confirmed = True
            self.destroy()
            if on_confirm:
                on_confirm()

        secondary_button(actions, "Cancelar", command=self.destroy).pack(side="right", padx=(8, 0))
        btn = danger_button if danger else primary_button
        btn(actions, confirm_text, command=_ok).pack(side="right")
        self.after(50, self.lift)
