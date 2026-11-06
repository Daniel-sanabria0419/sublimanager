# Desktop SubliManager

Cliente de escritorio (CustomTkinter). En **Stage 1** solo existe un stub (`main.py`).

La UI ERP se construye en **Stage 8**. El cliente **nunca** importa SQLAlchemy ni
conecta a PostgreSQL: toda comunicación es REST vía HTTPX contra el backend.
