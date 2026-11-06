"""Tarjetas KPI / superficie."""

from __future__ import annotations

import customtkinter as ctk

from desktop.styles import theme


class KpiCard(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        title: str,
        value: str = "—",
        *,
        accent: str = theme.PRIMARY,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=theme.SURFACE,
            corner_radius=10,
            border_width=1,
            border_color=theme.BORDER,
            **kwargs,
        )
        bar = ctk.CTkFrame(self, fg_color=accent, height=4, corner_radius=0)
        bar.pack(fill="x", padx=0, pady=0)
        self._title = ctk.CTkLabel(
            self, text=title, text_color=theme.TEXT_MUTED, font=theme.FONT_SMALL, anchor="w"
        )
        self._title.pack(fill="x", padx=14, pady=(10, 2))
        self._value = ctk.CTkLabel(
            self, text=value, text_color=theme.TEXT, font=theme.FONT_TITLE, anchor="w"
        )
        self._value.pack(fill="x", padx=14, pady=(0, 14))

    def set_value(self, value: str) -> None:
        self._value.configure(text=value)


class SurfaceCard(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(
            master,
            fg_color=theme.SURFACE,
            corner_radius=10,
            border_width=1,
            border_color=theme.BORDER,
            **kwargs,
        )
