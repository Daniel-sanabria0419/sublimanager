"""Punto de entrada del cliente desktop SubliManager.

Uso (desde la raíz del repositorio):

    python -m desktop.main

Variables de entorno:

    SUBLIMANAGER_API_URL  (default http://127.0.0.1:8000)
"""

from __future__ import annotations

import os
import sys


def _mensaje_sin_tkinter() -> str:
    return (
        "No se pudo cargar Tk (_tkinter). CustomTkinter lo necesita.\n"
        "\n"
        "En macOS con Python de Homebrew (3.12):\n"
        "  brew install python-tk@3.12\n"
        "Si sigue fallando: brew install tcl-tk\n"
        "Luego vuelva a intentar: python -m desktop.main\n"
        "\n"
        "En Debian/Ubuntu: sudo apt install python3-tk\n"
    )


def main() -> None:
    # Asegura que la raíz del monorepo esté en sys.path al ejecutar como script.
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if root not in sys.path:
        sys.path.insert(0, root)

    try:
        import tkinter  # noqa: F401 — fail-fast si falta _tkinter del sistema
        import customtkinter  # noqa: F401 — fail-fast si falta dependencia pip
    except ModuleNotFoundError as exc:
        name = getattr(exc, "name", None) or ""
        missing_tk = name in {"_tkinter", "tkinter"} or "_tkinter" in str(exc)
        if missing_tk:
            print(_mensaje_sin_tkinter(), file=sys.stderr)
            raise SystemExit(1) from exc
        raise

    from desktop.app import SubliManagerApp

    app = SubliManagerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
