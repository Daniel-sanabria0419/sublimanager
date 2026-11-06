"""Punto de entrada del cliente desktop SubliManager.

Uso (desde la raíz del repositorio):

    python -m desktop.main

Variables de entorno:

    SUBLIMANAGER_API_URL  (default http://127.0.0.1:8000)
"""

from __future__ import annotations

import os
import sys


def main() -> None:
    # Asegura que la raíz del monorepo esté en sys.path al ejecutar como script.
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if root not in sys.path:
        sys.path.insert(0, root)

    import customtkinter  # noqa: F401 — fail-fast si falta dependencia

    from desktop.app import SubliManagerApp

    app = SubliManagerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
