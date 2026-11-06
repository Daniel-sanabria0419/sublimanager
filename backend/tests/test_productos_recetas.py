"""Tests de integración Stage 4 — productos, recetas y costo estimado."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(
    __import__("os").getenv("TEST_DATABASE_URL") is None,
    reason="Requiere TEST_DATABASE_URL",
)

API = "/api/v1"


def _catalogo_inventario(client: TestClient) -> dict[str, int]:
    cat = client.post(
        f"{API}/categorias-material",
        json={"nombre": "Insumos", "descripcion": "Base"},
    )
    assert cat.status_code == 201, cat.text
    uni = client.post(
        f"{API}/unidades-medida",
        json={"nombre": "Unidad", "abreviatura": "u"},
    )
    assert uni.status_code == 201, uni.text
    bod = client.post(
        f"{API}/bodegas",
        json={"nombre": "Taller", "ubicacion": "Principal"},
    )
    assert bod.status_code == 201, bod.text
    return {
        "categoria_material_id": cat.json()["id"],
        "unidad_id": uni.json()["id"],
        "bodega_id": bod.json()["id"],
    }


def _material(
    client: TestClient,
    ids: dict[str, int],
    *,
    nombre: str,
    costo: str,
    stock: str = "100",
) -> dict:
    resp = client.post(
        f"{API}/materiales",
        json={
            "categoria_id": ids["categoria_material_id"],
            "unidad_id": ids["unidad_id"],
            "nombre": nombre,
            "stock_minimo": "1",
            "stock_inicial": stock,
            "bodega_id": ids["bodega_id"],
            "costo_unitario_inicial": costo,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _categoria_producto(client: TestClient, nombre: str = "Textiles") -> int:
    resp = client.post(
        f"{API}/categorias-producto",
        json={"nombre": nombre, "descripcion": "Cat productos"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _producto(
    client: TestClient,
    categoria_id: int,
    *,
    nombre: str,
    tipo: str,
) -> dict:
    resp = client.post(
        f"{API}/productos",
        json={
            "categoria_id": categoria_id,
            "nombre": nombre,
            "tipo_producto": tipo,
            "descripcion": f"Producto {tipo}",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["tipo_producto"] == tipo
    return body


# ---------------------------------------------------------------------------
# Tipos de producto
# ---------------------------------------------------------------------------


def test_productos_fabricado_reventa_servicio(api_client: TestClient) -> None:
    cat_id = _categoria_producto(api_client)
    fab = _producto(api_client, cat_id, nombre="Camiseta subli", tipo="FABRICADO")
    rev = _producto(api_client, cat_id, nombre="Gorra importada", tipo="REVENTA")
    srv = _producto(api_client, cat_id, nombre="Diseño logo", tipo="SERVICIO")

    lista = api_client.get(f"{API}/productos", params={"tipo_producto": "FABRICADO"})
    assert lista.status_code == 200
    ids = {p["id"] for p in lista.json()}
    assert fab["id"] in ids
    assert rev["id"] not in ids
    assert srv["id"] not in ids

    bad = api_client.post(
        f"{API}/productos",
        json={
            "categoria_id": cat_id,
            "nombre": "Inválido",
            "tipo_producto": "OTRO",
        },
    )
    assert bad.status_code == 422


# ---------------------------------------------------------------------------
# Variantes + SKU único
# ---------------------------------------------------------------------------


def test_variantes_sku_unico(api_client: TestClient) -> None:
    cat_id = _categoria_producto(api_client, "Variantes")
    prod = _producto(api_client, cat_id, nombre="Mug", tipo="FABRICADO")

    v1 = api_client.post(
        f"{API}/variantes-producto",
        json={
            "producto_id": prod["id"],
            "sku": "MUG-BL-11",
            "talla": "11oz",
            "color": "Blanco",
            "precio_venta": "25000.00",
            "control_stock": True,
        },
    )
    assert v1.status_code == 201, v1.text
    assert v1.json()["sku"] == "MUG-BL-11"
    assert Decimal(str(v1.json()["precio_venta"])) == Decimal("25000.00")

    dup = api_client.post(
        f"{API}/variantes-producto",
        json={
            "producto_id": prod["id"],
            "sku": "MUG-BL-11",
            "talla": "11oz",
            "color": "Negro",
            "precio_venta": "26000.00",
        },
    )
    assert dup.status_code == 409, dup.text
    assert dup.json()["codigo"] == "conflicto_negocio"

    v2 = api_client.post(
        f"{API}/variantes-producto",
        json={
            "producto_id": prod["id"],
            "sku": "MUG-NG-11",
            "color": "Negro",
            "precio_venta": "26000.50",
        },
    )
    assert v2.status_code == 201, v2.text

    listado = api_client.get(
        f"{API}/variantes-producto", params={"producto_id": prod["id"]}
    )
    assert listado.status_code == 200
    assert len(listado.json()) == 2


# ---------------------------------------------------------------------------
# Técnicas producto unique
# ---------------------------------------------------------------------------


def test_tecnicas_producto_unique(api_client: TestClient) -> None:
    cat_id = _categoria_producto(api_client, "Tecnicas")
    prod = _producto(api_client, cat_id, nombre="Playera", tipo="FABRICADO")
    tec = api_client.post(
        f"{API}/tecnicas-produccion",
        json={"nombre": "Sublimación plana", "descripcion": "Prensa plana"},
    )
    assert tec.status_code == 201, tec.text

    link = api_client.post(
        f"{API}/tecnicas-producto",
        json={"producto_id": prod["id"], "tecnica_id": tec.json()["id"]},
    )
    assert link.status_code == 201, link.text

    dup = api_client.post(
        f"{API}/tecnicas-producto",
        json={"producto_id": prod["id"], "tecnica_id": tec.json()["id"]},
    )
    assert dup.status_code == 409


# ---------------------------------------------------------------------------
# Recetas + versiones históricas
# ---------------------------------------------------------------------------


def test_recetas_versiones_historicas(api_client: TestClient) -> None:
    inv = _catalogo_inventario(api_client)
    mat = _material(api_client, inv, nombre="Papel transfer", costo="10.00")
    cat_id = _categoria_producto(api_client, "Recetas")
    prod = _producto(api_client, cat_id, nombre="Camisa", tipo="FABRICADO")

    r1 = api_client.post(
        f"{API}/recetas-producto",
        json={
            "producto_id": prod["id"],
            "nombre": "Receta v1",
            "activo": True,
            "items": [
                {
                    "material_id": mat["id"],
                    "cantidad": "1.5",
                    "porcentaje_desperdicio": "5",
                }
            ],
        },
    )
    assert r1.status_code == 201, r1.text
    assert r1.json()["version"] == 1
    assert r1.json()["activo"] is True
    assert len(r1.json()["items"]) == 1

    r2 = api_client.post(
        f"{API}/recetas-producto",
        json={
            "producto_id": prod["id"],
            "nombre": "Receta v2",
            "activo": True,
            "items": [
                {
                    "material_id": mat["id"],
                    "cantidad": "2.0",
                    "porcentaje_desperdicio": "8",
                }
            ],
        },
    )
    assert r2.status_code == 201, r2.text
    assert r2.json()["version"] == 2
    assert r2.json()["activo"] is True

    # v1 permanece en histórico, desactivada
    hist = api_client.get(f"{API}/recetas-producto/{r1.json()['id']}")
    assert hist.status_code == 200
    assert hist.json()["version"] == 1
    assert hist.json()["activo"] is False
    assert Decimal(str(hist.json()["items"][0]["cantidad"])) == Decimal("1.5000")

    # Reactivar v1 desactiva v2
    act = api_client.post(f"{API}/recetas-producto/{r1.json()['id']}/activar")
    assert act.status_code == 200
    assert act.json()["activo"] is True
    v2 = api_client.get(f"{API}/recetas-producto/{r2.json()['id']}")
    assert v2.json()["activo"] is False

    todas = api_client.get(
        f"{API}/recetas-producto",
        params={"producto_id": prod["id"], "solo_variante_exacta": True},
    )
    assert todas.status_code == 200
    assert len(todas.json()) == 2


# ---------------------------------------------------------------------------
# Perfiles de costo — historia
# ---------------------------------------------------------------------------


def test_perfiles_costo_conservan_historia(api_client: TestClient) -> None:
    cat_id = _categoria_producto(api_client, "Costos")
    prod = _producto(api_client, cat_id, nombre="Servicio plotter", tipo="SERVICIO")

    p1 = api_client.post(
        f"{API}/perfiles-costo-producto",
        json={
            "producto_id": prod["id"],
            "costo_mano_obra_por_unidad": "5.00",
            "costo_otros_por_unidad": "1.00",
            "activo": True,
        },
    )
    assert p1.status_code == 201, p1.text
    assert p1.json()["activo"] is True

    p2 = api_client.post(
        f"{API}/perfiles-costo-producto",
        json={
            "producto_id": prod["id"],
            "costo_mano_obra_por_unidad": "7.50",
            "costo_otros_por_unidad": "2.25",
            "activo": True,
        },
    )
    assert p2.status_code == 201, p2.text

    viejo = api_client.get(f"{API}/perfiles-costo-producto/{p1.json()['id']}")
    assert viejo.status_code == 200
    assert viejo.json()["activo"] is False
    assert Decimal(str(viejo.json()["costo_mano_obra_por_unidad"])) == Decimal("5.00")

    activos = api_client.get(
        f"{API}/perfiles-costo-producto",
        params={"producto_id": prod["id"], "activo": True},
    )
    assert len(activos.json()) == 1
    assert activos.json()[0]["id"] == p2.json()["id"]

    todos = api_client.get(
        f"{API}/perfiles-costo-producto",
        params={"producto_id": prod["id"]},
    )
    assert len(todos.json()) == 2


# ---------------------------------------------------------------------------
# Costo estimado Decimal (§5.4)
# ---------------------------------------------------------------------------


def test_costo_estimado_fabricado(api_client: TestClient) -> None:
    inv = _catalogo_inventario(api_client)
    tinta = _material(api_client, inv, nombre="Tinta CMYK", costo="20.00")
    papel = _material(api_client, inv, nombre="Papel A3", costo="5.00")
    cat_id = _categoria_producto(api_client, "CostoFab")
    prod = _producto(api_client, cat_id, nombre="Polera", tipo="FABRICADO")
    var = api_client.post(
        f"{API}/variantes-producto",
        json={
            "producto_id": prod["id"],
            "sku": "POL-M-AZ",
            "talla": "M",
            "color": "Azul",
            "precio_venta": "100.00",
        },
    )
    assert var.status_code == 201, var.text
    variante_id = var.json()["id"]

    # mat = 2*20*(1+10/100) + 1*5*(1+0/100) = 44 + 5 = 49
    receta = api_client.post(
        f"{API}/recetas-producto",
        json={
            "producto_id": prod["id"],
            "nombre": "BOM polera",
            "activo": True,
            "items": [
                {
                    "material_id": tinta["id"],
                    "cantidad": "2",
                    "porcentaje_desperdicio": "10",
                },
                {
                    "material_id": papel["id"],
                    "cantidad": "1",
                    "porcentaje_desperdicio": "0",
                },
            ],
        },
    )
    assert receta.status_code == 201, receta.text

    perfil = api_client.post(
        f"{API}/perfiles-costo-producto",
        json={
            "producto_id": prod["id"],
            "costo_mano_obra_por_unidad": "8.00",
            "costo_electricidad_por_unidad": "1.50",
            "costo_depreciacion_por_unidad": "0.50",
            "costo_otros_por_unidad": "1.00",
            "activo": True,
        },
    )
    assert perfil.status_code == 201, perfil.text

    # estimado = 49 + 8 + 1.50 + 0.50 + 1 = 60.00
    est = api_client.get(
        f"{API}/productos/{prod['id']}/costo-estimado",
        params={"variante_id": variante_id},
    )
    assert est.status_code == 200, est.text
    body = est.json()
    assert body["tipo_producto"] == "FABRICADO"
    assert Decimal(str(body["costo_materiales"])) == Decimal("49.00")
    assert Decimal(str(body["costo_mano_obra"])) == Decimal("8.00")
    assert Decimal(str(body["costo_electricidad"])) == Decimal("1.50")
    assert Decimal(str(body["costo_depreciacion"])) == Decimal("0.50")
    assert Decimal(str(body["costo_otros"])) == Decimal("1.00")
    assert Decimal(str(body["costo_estimado"])) == Decimal("60.00")
    assert Decimal(str(body["precio_venta"])) == Decimal("100.00")
    assert Decimal(str(body["utilidad"])) == Decimal("40.00")
    assert Decimal(str(body["margen_porcentaje"])) == Decimal("40.00")
    assert body["receta_id"] == receta.json()["id"]
    assert body["perfil_costo_id"] == perfil.json()["id"]


def test_costo_estimado_reventa(api_client: TestClient) -> None:
    cat_id = _categoria_producto(api_client, "CostoRev")
    prod = _producto(api_client, cat_id, nombre="Gorra stock", tipo="REVENTA")
    var = api_client.post(
        f"{API}/variantes-producto",
        json={
            "producto_id": prod["id"],
            "sku": "GORRA-01",
            "precio_venta": "45.00",
            "control_stock": True,
        },
    )
    assert var.status_code == 201
    variante_id = var.json()["id"]

    # Sin historial: override explícito
    est = api_client.get(
        f"{API}/productos/{prod['id']}/costo-estimado",
        params={"variante_id": variante_id, "costo_adquisicion": "18.75"},
    )
    assert est.status_code == 200, est.text
    body = est.json()
    assert body["tipo_producto"] == "REVENTA"
    assert Decimal(str(body["costo_estimado"])) == Decimal("18.75")
    assert Decimal(str(body["costo_materiales"])) == Decimal("0.00")
    assert Decimal(str(body["utilidad"])) == Decimal("26.25")

    # Con movimiento de compra confirmado de la variante
    inv = _catalogo_inventario(api_client)
    mov = api_client.post(
        f"{API}/movimientos-inventario",
        json={
            "tipo_movimiento": "COMPRA",
            "bodega_id": inv["bodega_id"],
            "items": [
                {
                    "variante_producto_id": variante_id,
                    "cantidad": "10",
                    "costo_unitario": "22.00",
                }
            ],
            "confirmar": True,
        },
    )
    assert mov.status_code == 201, mov.text

    est2 = api_client.get(
        f"{API}/productos/{prod['id']}/costo-estimado",
        params={"variante_id": variante_id},
    )
    assert est2.status_code == 200, est2.text
    assert Decimal(str(est2.json()["costo_estimado"])) == Decimal("22.00")


def test_costo_estimado_servicio(api_client: TestClient) -> None:
    cat_id = _categoria_producto(api_client, "CostoSrv")
    prod = _producto(api_client, cat_id, nombre="Diseño vector", tipo="SERVICIO")

    perfil = api_client.post(
        f"{API}/perfiles-costo-producto",
        json={
            "producto_id": prod["id"],
            "costo_mano_obra_por_unidad": "30.00",
            "costo_electricidad_por_unidad": "99.00",  # no entra en SERVICIO
            "costo_depreciacion_por_unidad": "50.00",  # no entra
            "costo_otros_por_unidad": "5.50",
            "activo": True,
        },
    )
    assert perfil.status_code == 201, perfil.text

    est = api_client.get(f"{API}/productos/{prod['id']}/costo-estimado")
    assert est.status_code == 200, est.text
    body = est.json()
    assert body["tipo_producto"] == "SERVICIO"
    assert Decimal(str(body["costo_mano_obra"])) == Decimal("30.00")
    assert Decimal(str(body["costo_otros"])) == Decimal("5.50")
    assert Decimal(str(body["costo_electricidad"])) == Decimal("0.00")
    assert Decimal(str(body["costo_depreciacion"])) == Decimal("0.00")
    assert Decimal(str(body["costo_estimado"])) == Decimal("35.50")
    assert body["receta_id"] is None


def test_categorias_costo_crud(api_client: TestClient) -> None:
    crear = api_client.post(
        f"{API}/categorias-costo",
        json={"nombre": "Mano de obra directa", "tipo_costo": "MANO_OBRA"},
    )
    assert crear.status_code == 201, crear.text
    assert crear.json()["tipo_costo"] == "MANO_OBRA"

    lista = api_client.get(f"{API}/categorias-costo")
    assert lista.status_code == 200
    assert any(c["id"] == crear.json()["id"] for c in lista.json())
