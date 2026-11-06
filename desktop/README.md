# Desktop SubliManager (Etapa 8)

Cliente ERP de escritorio con **CustomTkinter**. Toda la lógica de negocio vive en el backend; este cliente solo habla REST vía HTTPX.

## Requisitos

- Python 3.12+
- Backend FastAPI en marcha (`./scripts/run_api.sh`)
- Dependencias:

```bash
pip install -r desktop/requirements.txt
# En Debian/Ubuntu también: sudo apt install python3-tk
```

## Arranque

Desde la raíz del repositorio:

```bash
# Terminal 1 — API
./scripts/run_api.sh

# Terminal 2 — Desktop
export SUBLIMANAGER_API_URL=http://127.0.0.1:8000   # opcional
python -m desktop.main
```

## Arquitectura del cliente

```
desktop/
├── main.py              # punto de entrada
├── app.py               # shell: sidebar + top bar
├── api/client.py        # HTTPX (sin SQLAlchemy / sin DB)
├── components/          # tablas, botones, cards, toasts
├── dialogs/             # formularios y confirmaciones
├── styles/theme.py      # paleta §6
├── utils/async_ui.py    # HTTP fuera del hilo UI
└── views/               # pantallas por menú (español)
```

## Menú

GENERAL · VENTAS · PRODUCCIÓN · INVENTARIO · FINANZAS · REPORTES (stub Etapa 9) · CONFIGURACIÓN

## Reglas

- Textos de UI en español
- Sin reglas de negocio en las vistas
- Sin acceso directo a PostgreSQL
- Llamadas HTTP en hilos worker + actualización segura de Tk
