"""Toasts de éxito / error / info (español)."""

from __future__ import annotations

import customtkinter as ctk

from desktop.styles import theme


class ToastHost(ctk.CTkFrame):
    """Contenedor flotante en la esquina superior derecha del contenido."""

    def __init__(self, master: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._toasts: list[ctk.CTkFrame] = []

    def show(self, message: str, *, kind: str = "info", duration_ms: int = 3500) -> None:
        colors = {
            "success": (theme.SUCCESS, "#ECFDF5"),
            "error": (theme.ERROR, "#FEF2F2"),
            "warning": (theme.WARNING, "#FFFBEB"),
            "info": (theme.PRIMARY, "#EFF6FF"),
        }
        accent, bg = colors.get(kind, colors["info"])
        frame = ctk.CTkFrame(self, fg_color=bg, corner_radius=8, border_width=1, border_color=accent)
        label = ctk.CTkLabel(
            frame,
            text=message,
            text_color=theme.TEXT,
            font=theme.FONT_SMALL,
            wraplength=360,
            justify="left",
        )
        label.pack(padx=12, pady=10)
        frame.pack(fill="x", pady=(0, 6))
        self._toasts.append(frame)
        self.after(duration_ms, lambda f=frame: self._dismiss(f))

    def _dismiss(self, frame: ctk.CTkFrame) -> None:
        if frame in self._toasts:
            self._toasts.remove(frame)
        try:
            frame.destroy()
        except Exception:
            pass
