"""Helpers para llamadas HTTP fuera del hilo de Tkinter."""

from __future__ import annotations

import threading
import traceback
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


def run_async(
    widget: Any,
    work: Callable[[], T],
    *,
    on_success: Callable[[T], None] | None = None,
    on_error: Callable[[Exception], None] | None = None,
    on_finally: Callable[[], None] | None = None,
) -> None:
    """Ejecuta `work` en un hilo y programa callbacks en el hilo de UI."""

    def _runner() -> None:
        err: Exception | None = None
        result: Any = None
        try:
            result = work()
        except Exception as exc:  # noqa: BLE001 — superficie a UI
            err = exc
            # ApiError es esperado en UI; solo traza fallos inesperados
            from desktop.api.client import ApiError

            if not isinstance(exc, ApiError):
                traceback.print_exc()

        def _finish() -> None:
            try:
                if err is not None:
                    if on_error is not None:
                        on_error(err)
                elif on_success is not None:
                    on_success(result)
            finally:
                if on_finally is not None:
                    on_finally()

        try:
            widget.after(0, _finish)
        except Exception:  # widget destruido
            pass

    threading.Thread(target=_runner, daemon=True).start()
