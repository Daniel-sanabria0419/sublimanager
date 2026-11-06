"""Botones reutilizables."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from desktop.styles import theme


def primary_button(master: ctk.CTkBaseClass, text: str, command: Callable[[], None] | None = None) -> ctk.CTkButton:
    return ctk.CTkButton(
        master,
        text=text,
        command=command,
        fg_color=theme.PRIMARY,
        hover_color="#1D4ED8",
        text_color="#FFFFFF",
        font=theme.FONT_BODY,
        corner_radius=8,
        height=36,
    )


def secondary_button(master: ctk.CTkBaseClass, text: str, command: Callable[[], None] | None = None) -> ctk.CTkButton:
    return ctk.CTkButton(
        master,
        text=text,
        command=command,
        fg_color=theme.SURFACE,
        hover_color=theme.BORDER,
        text_color=theme.TEXT,
        border_width=1,
        border_color=theme.BORDER,
        font=theme.FONT_BODY,
        corner_radius=8,
        height=36,
    )


def danger_button(master: ctk.CTkBaseClass, text: str, command: Callable[[], None] | None = None) -> ctk.CTkButton:
    return ctk.CTkButton(
        master,
        text=text,
        command=command,
        fg_color=theme.ERROR,
        hover_color="#B91C1C",
        text_color="#FFFFFF",
        font=theme.FONT_BODY,
        corner_radius=8,
        height=36,
    )


def success_button(master: ctk.CTkBaseClass, text: str, command: Callable[[], None] | None = None) -> ctk.CTkButton:
    return ctk.CTkButton(
        master,
        text=text,
        command=command,
        fg_color=theme.SUCCESS,
        hover_color="#15803D",
        text_color="#FFFFFF",
        font=theme.FONT_BODY,
        corner_radius=8,
        height=36,
    )
