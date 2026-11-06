"""Tests de integración Stage 3 — inventario y compras (HTTPX / TestClient)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(
    __import__("os").getenv("TEST_DATABASE_URL") is None,
    reason="Requiere TEST_DATABASE_URL",
)

API = "/api/v1"


def _bootstrap_catalogo(client: TestClient) -> dict[str, int]:
    cat = client.post(
        f"{API}/categorias-material",
        json={"nombre": "Tintas", "descripcion": "Tintas sublimación"},
    )
    assert cat.status_code == 201, cat.text
    uni = client.post(
        f"{API}/unidades-medida",
        json={"nombre": "Kilogramo", "abreviatura": "kg"},
    )
    assert uni.status_code == 201, uni.text
    bod = client.post(
        f"{API}/bodegas",
        json={"nombre": "Principal", "ubicacion": "Taller"},
    )
    assert bod.status_code == 201, bod.text
    bod2 = client.post(
        f"{API}/bodegas",
        json={"nombre": "Secundaria", "ubicacion": "Anexo"},
    )
    assert bod2.status_code == 201, bod2.text
    prov = client.post(
        f"{API}/proveedores",
        json={"nombre": "Proveedor Test", "identificacion": "900123"},
    )
    assert prov.status_code == 201, prov.text
    return {
        "categoria_id": cat.json()["id"],
        "unidad_id": uni.json()["id"],
        "bodega_id": bod.json()["id"],
        "bodega2_id": bod2.json()["id"],
        "proveedor_id": prov.json()["id"],
    }


def _crear_material(
    client: TestClient,
    ids: dict[str, int],
    *,
    nombre: str = "Papel A4",
    stock_minimo: str = "10",
    stock_inicial: str | None = None,
    costo: str | None = None,
) -> dict:
    payload: dict = {
        "categoria_id": ids["categoria_id"],
        "unidad_id": ids["unidad_id"],
        "nombre": nombre,
        "stock_minimo": stock_minimo,
    }
    if stock_inicial is not None:
        payload["stock_inicial"] = stock_inicial
        payload["bodega_id"] = ids["bodega_id"]
        payload["costo_unitario_inicial"] = costo or "0"
    resp = client.post(f"{API}/materiales", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _stock_material(client: TestClient, material_id: int) -> Decimal:
    resp = client.get(f"{API}/existencias", params={"material_id": material_id})
    assert resp.status_code == 200
    total = Decimal("0")
    for row in resp.json():
        total += Decimal(str(row["cantidad"]))
    return total


def test_recepcion_compra_aumenta_stock(api_client: TestClient) -> None:
    ids = _bootstrap_catalogo(api_client)
    mat = _crear_material(api_client, ids, stock_inicial=None)
    assert _stock_material(api_client, mat["id"]) == Decimal("0")

    compra = api_client.post(
        f"{API}/compras",
        json={
            "proveedor_id": ids["proveedor_id"],
            "items": [
                {
                    "material_id": mat["id"],
                    "cantidad": "100",
                    "costo_unitario": "10.00",
                }
            ],
        },
    )
    assert compra.status_code == 201, compra.text
    body = compra.json()
    assert body["estado"] == "BORRADOR"
    assert _stock_material(api_client, mat["id"]) == Decimal("0")

    recibo = api_client.post(
        f"{API}/compras/{body['id']}/recibir",
        json={"bodega_id": ids["bodega_id"]},
    )
    assert recibo.status_code == 200, recibo.text
    assert recibo.json()["estado"] == "RECIBIDA"
    assert _stock_material(api_client, mat["id"]) == Decimal("100.0000")

    mat_refresco = api_client.get(f"{API}/materiales/{mat['id']}")
    assert mat_refresco.status_code == 200
    assert Decimal(str(mat_refresco.json()["costo_promedio"])) == Decimal("10.00")


def test_salida_produccion_y_ajuste(api_client: TestClient) -> None:
    ids = _bootstrap_catalogo(api_client)
    mat = _crear_material(
        api_client, ids, stock_inicial="50", costo="5.00"
    )
    assert _stock_material(api_client, mat["id"]) == Decimal("50.0000")

    salida = api_client.post(
        f"{API}/movimientos-inventario",
        json={
            "tipo_movimiento": "PRODUCCION",
            "bodega_id": ids["bodega_id"],
            "items": [
                {
                    "material_id": mat["id"],
                    "cantidad": "12.5",
                    "costo_unitario": "5.00",
                }
            ],
            "confirmar": True,
        },
    )
    assert salida.status_code == 201, salida.text
    assert salida.json()["estado"] == "CONFIRMADO"
    assert _stock_material(api_client, mat["id"]) == Decimal("37.5000")

    ajuste = api_client.post(
        f"{API}/movimientos-inventario",
        json={
            "tipo_movimiento": "AJUSTE",
            "bodega_id": ids["bodega_id"],
            "items": [
                {
                    "material_id": mat["id"],
                    "cantidad": "2.5",
                    "costo_unitario": "5.00",
                }
            ],
        },
    )
    assert ajuste.status_code == 201, ajuste.text
    assert _stock_material(api_client, mat["id"]) == Decimal("40.0000")


def test_stock_negativo_rechazado(api_client: TestClient) -> None:
    ids = _bootstrap_catalogo(api_client)
    mat = _crear_material(api_client, ids, stock_inicial="10", costo="1")
    resp = api_client.post(
        f"{API}/movimientos-inventario",
        json={
            "tipo_movimiento": "PRODUCCION",
            "bodega_id": ids["bodega_id"],
            "items": [
                {
                    "material_id": mat["id"],
                    "cantidad": "10.0001",
                    "costo_unitario": "1.00",
                }
            ],
        },
    )
    assert resp.status_code == 409, resp.text
    assert _stock_material(api_client, mat["id"]) == Decimal("10.0000")


def test_costo_promedio_ponderado(api_client: TestClient) -> None:
    ids = _bootstrap_catalogo(api_client)
    mat = _crear_material(
        api_client, ids, stock_inicial="100", costo="10.00"
    )
    assert Decimal(str(mat["costo_promedio"])) == Decimal("10.00")

    compra = api_client.post(
        f"{API}/compras",
        json={
            "proveedor_id": ids["proveedor_id"],
            "items": [
                {
                    "material_id": mat["id"],
                    "cantidad": "100",
                    "costo_unitario": "20.00",
                }
            ],
        },
    ).json()
    api_client.post(
        f"{API}/compras/{compra['id']}/recibir",
        json={"bodega_id": ids["bodega_id"]},
    )
    mat2 = api_client.get(f"{API}/materiales/{mat['id']}").json()
    assert Decimal(str(mat2["costo_promedio"])) == Decimal("15.00")
    assert _stock_material(api_client, mat["id"]) == Decimal("200.0000")


def test_cancelacion_compra_reglas(api_client: TestClient) -> None:
    ids = _bootstrap_catalogo(api_client)
    mat = _crear_material(api_client, ids)

    # BORRADOR se puede cancelar y no toca stock
    compra = api_client.post(
        f"{API}/compras",
        json={
            "proveedor_id": ids["proveedor_id"],
            "items": [
                {
                    "material_id": mat["id"],
                    "cantidad": "30",
                    "costo_unitario": "8.00",
                }
            ],
        },
    ).json()
    cancel = api_client.post(f"{API}/compras/{compra['id']}/cancelar")
    assert cancel.status_code == 200
    assert cancel.json()["estado"] == "CANCELADA"
    assert _stock_material(api_client, mat["id"]) == Decimal("0")

    # CANCELADA no puede recibir
    recibir = api_client.post(
        f"{API}/compras/{compra['id']}/recibir",
        json={"bodega_id": ids["bodega_id"]},
    )
    assert recibir.status_code == 409

    # Tras recepción no se puede cancelar (exige REVERSO)
    compra2 = api_client.post(
        f"{API}/compras",
        json={
            "proveedor_id": ids["proveedor_id"],
            "items": [
                {
                    "material_id": mat["id"],
                    "cantidad": "5",
                    "costo_unitario": "8.00",
                }
            ],
        },
    ).json()
    rec = api_client.post(
        f"{API}/compras/{compra2['id']}/recibir",
        json={"bodega_id": ids["bodega_id"]},
    )
    assert rec.status_code == 200
    assert rec.json()["estado"] == "RECIBIDA"
    cancel2 = api_client.post(f"{API}/compras/{compra2['id']}/cancelar")
    assert cancel2.status_code == 409
    assert "REVERSO" in cancel2.json()["detalle"]


def test_recepcion_parcial(api_client: TestClient) -> None:
    ids = _bootstrap_catalogo(api_client)
    mat = _crear_material(api_client, ids)
    compra = api_client.post(
        f"{API}/compras",
        json={
            "proveedor_id": ids["proveedor_id"],
            "items": [
                {
                    "material_id": mat["id"],
                    "cantidad": "100",
                    "costo_unitario": "4.00",
                }
            ],
        },
    ).json()
    item_id = compra["items"][0]["id"]

    parcial = api_client.post(
        f"{API}/compras/{compra['id']}/recibir",
        json={
            "bodega_id": ids["bodega_id"],
            "items": [{"item_compra_id": item_id, "cantidad": "40"}],
        },
    )
    assert parcial.status_code == 200, parcial.text
    assert parcial.json()["estado"] == "PARCIALMENTE_RECIBIDA"
    assert _stock_material(api_client, mat["id"]) == Decimal("40.0000")

    resto = api_client.post(
        f"{API}/compras/{compra['id']}/recibir",
        json={"bodega_id": ids["bodega_id"]},
    )
    assert resto.status_code == 200
    assert resto.json()["estado"] == "RECIBIDA"
    assert _stock_material(api_client, mat["id"]) == Decimal("100.0000")


def test_alerta_stock_bajo(api_client: TestClient) -> None:
    ids = _bootstrap_catalogo(api_client)
    mat = _crear_material(
        api_client,
        ids,
        stock_minimo="20",
        stock_inicial="5",
        costo="1",
    )
    alertas = api_client.get(f"{API}/materiales/alertas-stock-bajo")
    assert alertas.status_code == 200
    ids_alerta = {a["material_id"] for a in alertas.json()}
    assert mat["id"] in ids_alerta


def test_transferencia_entre_bodegas(api_client: TestClient) -> None:
    ids = _bootstrap_catalogo(api_client)
    mat = _crear_material(
        api_client, ids, stock_inicial="30", costo="2"
    )
    resp = api_client.post(
        f"{API}/movimientos-inventario/transferencias",
        json={
            "bodega_origen_id": ids["bodega_id"],
            "bodega_destino_id": ids["bodega2_id"],
            "items": [
                {
                    "material_id": mat["id"],
                    "cantidad": "10",
                    "costo_unitario": "2.00",
                }
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["salida"]["grupo_transferencia_id"] == data["entrada"][
        "grupo_transferencia_id"
    ]
    orig = api_client.get(
        f"{API}/existencias",
        params={"material_id": mat["id"], "bodega_id": ids["bodega_id"]},
    ).json()
    dest = api_client.get(
        f"{API}/existencias",
        params={"material_id": mat["id"], "bodega_id": ids["bodega2_id"]},
    ).json()
    assert Decimal(str(orig[0]["cantidad"])) == Decimal("20.0000")
    assert Decimal(str(dest[0]["cantidad"])) == Decimal("10.0000")


def test_crud_catalogos(api_client: TestClient) -> None:
    cat = api_client.post(
        f"{API}/categorias-material", json={"nombre": "Vinilos"}
    )
    assert cat.status_code == 201
    cid = cat.json()["id"]
    assert api_client.get(f"{API}/categorias-material/{cid}").status_code == 200
    upd = api_client.patch(
        f"{API}/categorias-material/{cid}", json={"descripcion": "Rollos"}
    )
    assert upd.status_code == 200
    assert upd.json()["descripcion"] == "Rollos"
