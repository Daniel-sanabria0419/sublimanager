"""Smoke tests de /health y arranque de la app."""

from fastapi.testclient import TestClient


def test_app_inicia(client: TestClient) -> None:
    assert client.app is not None
    assert client.app.title == "SubliManager"


def test_health_ok(client: TestClient) -> None:
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "ok"
    assert cuerpo["aplicacion"] == "SubliManager"


def test_health_db_sin_postgres_devuelve_503_o_200(
    client: TestClient, test_database_url: str | None
) -> None:
    """Sin TEST_DATABASE_URL / PG local, /health/db puede fallar con 503.

    Con PG disponible se espera 200. No fallamos el suite si no hay BD.
    """
    respuesta = client.get("/health/db")
    if test_database_url:
        assert respuesta.status_code == 200
        assert respuesta.json()["estado"] == "ok"
    else:
        assert respuesta.status_code in (200, 503)
