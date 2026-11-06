"""Gráficos Matplotlib embebidos en CustomTkinter (Stage 9)."""

from __future__ import annotations

from typing import Sequence

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from desktop.styles import theme


class ChartPanel(ctk.CTkFrame):
    """Contenedor de un gráfico Matplotlib (sin lógica de negocio)."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        title: str,
        *,
        height: int = 220,
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
        ctk.CTkLabel(
            self,
            text=title,
            font=theme.FONT_SECTION,
            text_color=theme.TEXT,
            anchor="w",
        ).pack(fill="x", padx=12, pady=(10, 4))

        self._fig = Figure(figsize=(5.2, 2.4), dpi=100, facecolor=theme.SURFACE)
        self._ax = self._fig.add_subplot(111)
        self._ax.set_facecolor(theme.SURFACE)
        self._canvas = FigureCanvasTkAgg(self._fig, master=self)
        widget = self._canvas.get_tk_widget()
        widget.configure(height=height, background=theme.SURFACE, highlightthickness=0)
        widget.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._fig.tight_layout()

    def clear(self) -> None:
        self._ax.clear()
        self._ax.set_facecolor(theme.SURFACE)
        self._canvas.draw_idle()

    def plot_bars(
        self,
        labels: Sequence[str],
        values: Sequence[float],
        *,
        color: str = theme.PRIMARY,
        ylabel: str = "",
    ) -> None:
        self._ax.clear()
        self._ax.set_facecolor(theme.SURFACE)
        if not labels:
            self._ax.text(0.5, 0.5, "Sin datos", ha="center", va="center", color=theme.TEXT_MUTED)
            self._ax.set_xticks([])
            self._ax.set_yticks([])
        else:
            x = list(range(len(labels)))
            self._ax.bar(x, list(values), color=color)
            self._ax.set_xticks(x)
            self._ax.set_xticklabels(list(labels), rotation=30, ha="right", fontsize=8)
            if ylabel:
                self._ax.set_ylabel(ylabel, fontsize=8)
            self._ax.tick_params(colors=theme.TEXT_MUTED, labelsize=8)
            for spine in self._ax.spines.values():
                spine.set_color(theme.BORDER)
        self._fig.tight_layout()
        self._canvas.draw_idle()

    def plot_lines(
        self,
        labels: Sequence[str],
        series: dict[str, Sequence[float]],
        *,
        colors: dict[str, str] | None = None,
    ) -> None:
        self._ax.clear()
        self._ax.set_facecolor(theme.SURFACE)
        if not labels:
            self._ax.text(0.5, 0.5, "Sin datos", ha="center", va="center", color=theme.TEXT_MUTED)
            self._ax.set_xticks([])
            self._ax.set_yticks([])
        else:
            x = list(range(len(labels)))
            palette = colors or {}
            default_colors = [theme.PRIMARY, theme.ERROR, theme.SUCCESS, theme.WARNING]
            for i, (name, vals) in enumerate(series.items()):
                color = palette.get(name, default_colors[i % len(default_colors)])
                self._ax.plot(x, list(vals), marker="o", label=name, color=color, linewidth=1.8)
            self._ax.set_xticks(x)
            self._ax.set_xticklabels(list(labels), rotation=30, ha="right", fontsize=8)
            self._ax.legend(fontsize=8, loc="upper left")
            self._ax.tick_params(colors=theme.TEXT_MUTED, labelsize=8)
            for spine in self._ax.spines.values():
                spine.set_color(theme.BORDER)
        self._fig.tight_layout()
        self._canvas.draw_idle()
