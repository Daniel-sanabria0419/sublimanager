"""Tests de integración Stage 6 — órdenes de producción."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(
    __import__("os").getenv("TEST_DATABASE_URL") is None,
    reason="Requiere TEST_DATABASE_URL",
)

API = "/api/v1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _catalogo_inventario(client: TestClient, sufijo: str = "OP") -> dict[str, int]:
    cat = client.post(
        f"{API}/categorias-material",
        json={"nombre": f"Insumos {sufijo}", "descripcion": "Base"},
    )
    assert cat.status_code == 201, cat.text
    uni = client.post(
        f"{API}/unidades-medida",
        json={"nombre": f"Unidad {sufijo}", "abreviatura": sufijo[:3].lower()},
    )
    assert uni.status_code == 201, uni.text
    bod = client.post(
        f"{API}/bodegas",
        json={"nombre": f"Bodega {sufijo}", "ubicacion": "Taller"},
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


def _stock_material(
    client: TestClient, *, bodega_id: int, material_id: int
) -> Decimal:
    resp = client.get(
        f"{API}/existencias",
        params={"bodega_id": bodega_id, "material_id": material_id},
    )
    assert resp.status_code == 200, resp.text
    filas = resp.json()
    if not filas:
        return Decimal("0")
    return Decimal(str(filas[0]["cantidad"]))


def _stock_variante(
    client: TestClient, *, bodega_id: int, variante_id: int
) -> Decimal:
    resp = client.get(f"{API}/existencias", params={"bodega_id": bodega_id})
    assert resp.status_code == 200, resp.text
    for fila in resp.json():
        if fila.get("variante_producto_id") == variante_id:
            return Decimal(str(fila["cantidad"]))
    return Decimal("0")


def _cliente(client: TestClient, nombre: str = "Cliente OP") -> dict:
    resp = client.post(
        f"{API}/clientes",
        json={"nombre": nombre, "identificacion": "800111"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _categoria_producto(client: TestClient, nombre: str) -> int:
    resp = client.post(
        f"{API}/categorias-producto",
        json={"nombre": nombre, "descripcion": "Cat"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _producto(
    client: TestClient, categoria_id: int, *, nombre: str, tipo: str
) -> dict:
    resp = client.post(
        f"{API}/productos",
        json={
            "categoria_id": categoria_id,
            "nombre": nombre,
            "tipo_producto": tipo,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _variante(
    client: TestClient,
    producto_id: int,
    *,
    sku: str,
    precio: str,
    control_stock: bool = True,
) -> dict:
    resp = client.post(
        f"{API}/variantes-producto",
        json={
            "producto_id": producto_id,
            "sku": sku,
            "talla": "M",
            "color": "Blanco",
            "precio_venta": precio,
            "control_stock": control_stock,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _receta_y_perfil(
    client: TestClient,
    *,
    producto_id: int,
    material_id: int,
    qty_mat: str = "2",
    desperdicio: str = "10",
    mano_obra: str = "8.00",
    electricidad: str = "1.00",
    depreciacion: str = "0.50",
) -> None:
    receta = client.post(
        f"{API}/recetas-producto",
        json={
            "producto_id": producto_id,
            "nombre": "BOM OP",
            "activo": True,
            "items": [
                {
                    "material_id": material_id,
                    "cantidad": qty_mat,
                    "porcentaje_desperdicio": desperdicio,
                }
            ],
        },
    )
    assert receta.status_code == 201, receta.text
    perfil = client.post(
        f"{API}/perfiles-costo-producto",
        json={
            "producto_id": producto_id,
            "costo_mano_obra_por_unidad": mano_obra,
            "costo_electricidad_por_unidad": electricidad,
            "costo_depreciacion_por_unidad": depreciacion,
            "costo_otros_por_unidad": "0",
            "activo": True,
        },
    )
    assert perfil.status_code == 201, perfil.text


def _pedido_fabricado(client: TestClient, *, sufijo: str = "A") -> dict:
    """Escenario: pedido CONFIRMADO con 1 ítem FABRICADO (qty 10)."""
    inv = _catalogo_inventario(client, sufijo=sufijo)
    mat = _material(
        client, inv, nombre=f"Vinilo {sufijo}", costo="5.00", stock="200"
    )
    cat_id = _categoria_producto(client, f"Cat {sufijo}")
    fab = _producto(client, cat_id, nombre=f"Camiseta {sufijo}", tipo="FABRICADO")
    fab_v = _variante(
        client, fab["id"], sku=f"CAM-{sufijo}", precio="40000.00"
    )
    _receta_y_perfil(
        client,
        producto_id=fab["id"],
        material_id=mat["id"],
        qty_mat="2",
        desperdicio="10",
        mano_obra="8.00",
    )
    # estimado unitario mat = 2*5*1.10 = 11; +8 +1 +0.50 = 20.50

    cli = _cliente(client, nombre=f"Cliente {sufijo}")
    pedido = client.post(
        f"{API}/pedidos",
        json={
            "cliente_id": cli["id"],
            "items": [
                {
                    "producto_id": fab["id"],
                    "variante_id": fab_v["id"],
                    "cantidad": "10",
                }
            ],
        },
    )
    assert pedido.status_code == 201, pedido.text
    conf = client.post(
        f"{API}/pedidos/{pedido.json()['id']}/estado",
        json={"estado_nuevo": "CONFIRMADO"},
    )
    assert conf.status_code == 200, conf.text

    return {
        "inv": inv,
        "material": mat,
        "producto": fab,
        "variante": fab_v,
        "pedido": conf.json(),
        "item_pedido_id": conf.json()["items"][0]["id"],
        "bodega_id": inv["bodega_id"],
    }


def _crear_op(client: TestClient, esc: dict, *, qty: str | None = None) -> dict:
    item: dict = {"item_pedido_id": esc["item_pedido_id"]}
    if qty is not None:
        item["cantidad_planificada"] = qty
    resp = client.post(
        f"{API}/ordenes-produccion",
        json={
            "pedido_id": esc["pedido"]["id"],
            "items": [item],
            "notas": "OP test",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["pedido_id"] == esc["pedido"]["id"]
    assert body["estado"] == "PLANIFICADA"
    assert body["items"]
    return body


def _categoria_costo(
    client: TestClient, *, nombre: str, tipo: str
) -> dict:
    resp = client.post(
        f"{API}/categorias-costo",
        json={"nombre": nombre, "tipo_costo": tipo},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Flujo completo
# ---------------------------------------------------------------------------


def test_produccion_completa_con_pt_y_costos(api_client: TestClient) -> None:
    esc = _pedido_fabricado(api_client, sufijo="FULL")
    op = _crear_op(api_client, esc, qty="10")
    item_id = op["items"][0]["id"]
    bodega = esc["bodega_id"]
    mat_id = esc["material"]["id"]

    stock_ini = _stock_material(api_client, bodega_id=bodega, material_id=mat_id)
    assert stock_ini == Decimal("200")

    req = api_client.get(
        f"{API}/ordenes-produccion/{op['id']}/materiales-requeridos",
        params={"bodega_id": bodega},
    )
    assert req.status_code == 200, req.text
    body_req = req.json()
    assert body_req["todos_suficientes"] is True
    # 2 * 1.10 * 10 = 22
    assert Decimal(str(body_req["materiales"][0]["cantidad_requerida"])) == Decimal(
        "22.0000"
    )

    ini = api_client.post(f"{API}/ordenes-produccion/{op['id']}/iniciar")
    assert ini.status_code == 200, ini.text
    assert ini.json()["estado"] == "EN_PROCESO"
    assert ini.json()["fecha_inicio"] is not None

    # Consumo productivo 20 + desperdicio 2 = 22
    c1 = api_client.post(
        f"{API}/ordenes-produccion/{op['id']}/items/{item_id}/consumos",
        params={"bodega_id": bodega},
        json={
            "material_id": mat_id,
            "cantidad_consumida": "20",
            "es_desperdicio": False,
        },
    )
    assert c1.status_code == 201, c1.text
    assert Decimal(str(c1.json()["costo_total"])) == Decimal("100.00")

    c2 = api_client.post(
        f"{API}/ordenes-produccion/{op['id']}/items/{item_id}/consumos",
        params={"bodega_id": bodega},
        json={
            "material_id": mat_id,
            "cantidad_consumida": "2",
            "es_desperdicio": True,
            "notas": "Recorte",
        },
    )
    assert c2.status_code == 201, c2.text
    assert c2.json()["es_desperdicio"] is True

    stock_fin = _stock_material(api_client, bodega_id=bodega, material_id=mat_id)
    assert stock_fin == Decimal("178.0000")  # 200 - 22

    cat_mo = _categoria_costo(
        api_client, nombre="MO Full", tipo="MANO_OBRA"
    )
    asiento = api_client.post(
        f"{API}/ordenes-produccion/{op['id']}/items/{item_id}/asientos-costo",
        json={
            "categoria_costo_id": cat_mo["id"],
            "cantidad": "10",
            "costo_unitario": "9.00",
            "descripcion": "Mano de obra real",
        },
    )
    assert asiento.status_code == 201, asiento.text
    assert Decimal(str(asiento.json()["costo_total"])) == Decimal("90.00")

    # Rechazo de MATERIAL manual
    cat_mat = _categoria_costo(
        api_client, nombre="Mat Full", tipo="MATERIAL"
    )
    bad = api_client.post(
        f"{API}/ordenes-produccion/{op['id']}/items/{item_id}/asientos-costo",
        json={
            "categoria_costo_id": cat_mat["id"],
            "cantidad": "1",
            "costo_unitario": "10",
        },
    )
    assert bad.status_code == 400, bad.text

    cant = api_client.post(
        f"{API}/ordenes-produccion/{op['id']}/items/{item_id}/cantidades",
        json={
            "cantidad_producida": "9",
            "cantidad_rechazada": "1",
            "bodega_producto_id": bodega,
        },
    )
    assert cant.status_code == 200, cant.text
    assert Decimal(str(cant.json()["cantidad_producida"])) == Decimal("9.0000")
    assert Decimal(str(cant.json()["cantidad_rechazada"])) == Decimal("1.0000")

    stock_pt = _stock_variante(
        api_client, bodega_id=bodega, variante_id=esc["variante"]["id"]
    )
    assert stock_pt == Decimal("9.0000")

    cierre = api_client.post(
        f"{API}/ordenes-produccion/{op['id']}/completar",
        json={"bodega_producto_id": bodega},
    )
    assert cierre.status_code == 200, cierre.text
    assert cierre.json()["estado"] == "COMPLETADA"
    assert cierre.json()["fecha_fin"] is not None

    # Asiento MATERIAL REAL consolidado
    mats = [
        a
        for a in cierre.json()["items"][0]["asientos_costo"]
        if a["etapa_costo"] == "REAL"
    ]
    assert mats
    # 20*5 + 2*5 = 110 de materiales en consumos
    cmp_ = api_client.get(
        f"{API}/ordenes-produccion/{op['id']}/comparacion-costos"
    )
    assert cmp_.status_code == 200, cmp_.text
    body_cmp = cmp_.json()
    assert Decimal(str(body_cmp["costo_estimado_total"])) > 0
    assert Decimal(str(body_cmp["costo_real_total"])) > 0
    assert Decimal(str(body_cmp["items"][0]["costo_materiales_consumos"])) == Decimal(
        "110.00"
    )


def test_produccion_parcial(api_client: TestClient) -> None:
    esc = _pedido_fabricado(api_client, sufijo="PAR")
    op = _crear_op(api_client, esc, qty="10")
    item_id = op["items"][0]["id"]
    bodega = esc["bodega_id"]

    assert (
        api_client.post(f"{API}/ordenes-produccion/{op['id']}/iniciar").status_code
        == 200
    )

    # Solo 4 unidades planificadas efectivas vía cantidades parciales
    cons = api_client.post(
        f"{API}/ordenes-produccion/{op['id']}/items/{item_id}/consumos",
        params={"bodega_id": bodega},
        json={
            "material_id": esc["material"]["id"],
            "cantidad_consumida": "8.8",  # 2*1.1*4
        },
    )
    assert cons.status_code == 201, cons.text

    cant = api_client.post(
        f"{API}/ordenes-produccion/{op['id']}/items/{item_id}/cantidades",
        json={"cantidad_producida": "4", "cantidad_rechazada": "0"},
    )
    assert cant.status_code == 200, cant.text
    assert Decimal(str(cant.json()["cantidad_producida"])) == Decimal("4.0000")
    assert Decimal(str(cant.json()["cantidad_planificada"])) == Decimal("10.0000")

    cierre = api_client.post(f"{API}/ordenes-produccion/{op['id']}/completar")
    assert cierre.status_code == 200
    assert cierre.json()["estado"] == "COMPLETADA"
    assert Decimal(str(cierre.json()["items"][0]["cantidad_producida"])) == Decimal(
        "4.0000"
    )


def test_stock_insuficiente_bloquea_consumo(api_client: TestClient) -> None:
    esc = _pedido_fabricado(api_client, sufijo="INS")
    # Stock bajo: dejar solo 5 unidades
    # Recreamos escenario con stock bajo
    inv = _catalogo_inventario(api_client, sufijo="INS2")
    mat = _material(
        api_client, inv, nombre="Vinilo INS2", costo="5.00", stock="5"
    )
    cat_id = _categoria_producto(api_client, "Cat INS2")
    fab = _producto(api_client, cat_id, nombre="Cam INS2", tipo="FABRICADO")
    fab_v = _variante(api_client, fab["id"], sku="CAM-INS2", precio="10000")
    _receta_y_perfil(
        api_client,
        producto_id=fab["id"],
        material_id=mat["id"],
        qty_mat="2",
        desperdicio="0",
    )
    cli = _cliente(api_client, "Cli INS2")
    pedido = api_client.post(
        f"{API}/pedidos",
        json={
            "cliente_id": cli["id"],
            "items": [
                {
                    "producto_id": fab["id"],
                    "variante_id": fab_v["id"],
                    "cantidad": "10",
                }
            ],
        },
    ).json()
    api_client.post(
        f"{API}/pedidos/{pedido['id']}/estado",
        json={"estado_nuevo": "CONFIRMADO"},
    )
    op = api_client.post(
        f"{API}/ordenes-produccion",
        json={
            "pedido_id": pedido["id"],
            "items": [{"item_pedido_id": pedido["items"][0]["id"]}],
        },
    ).json()

    req = api_client.get(
        f"{API}/ordenes-produccion/{op['id']}/materiales-requeridos",
        params={"bodega_id": inv["bodega_id"]},
    )
    assert req.status_code == 200
    assert req.json()["todos_suficientes"] is False

    api_client.post(f"{API}/ordenes-produccion/{op['id']}/iniciar")
    item_id = op["items"][0]["id"]
    bad = api_client.post(
        f"{API}/ordenes-produccion/{op['id']}/items/{item_id}/consumos",
        params={"bodega_id": inv["bodega_id"]},
        json={"material_id": mat["id"], "cantidad_consumida": "20"},
    )
    assert bad.status_code == 409, bad.text
    assert bad.json()["codigo"] == "conflicto_negocio"
    # Stock intacto
    assert _stock_material(
        api_client, bodega_id=inv["bodega_id"], material_id=mat["id"]
    ) == Decimal("5.0000")


def test_desperdicio_y_rechazos(api_client: TestClient) -> None:
    esc = _pedido_fabricado(api_client, sufijo="DES")
    op = _crear_op(api_client, esc, qty="5")
    item_id = op["items"][0]["id"]
    bodega = esc["bodega_id"]
    api_client.post(f"{API}/ordenes-produccion/{op['id']}/iniciar")

    cons = api_client.post(
        f"{API}/ordenes-produccion/{op['id']}/items/{item_id}/consumos",
        params={"bodega_id": bodega},
        json={
            "material_id": esc["material"]["id"],
            "cantidad_consumida": "3",
            "es_desperdicio": True,
        },
    )
    assert cons.status_code == 201
    assert cons.json()["es_desperdicio"] is True

    # Movimiento DESPERDICIO confirmado
    movs = api_client.get(
        f"{API}/movimientos-inventario",
        params={"tipo_movimiento": "DESPERDICIO", "bodega_id": bodega},
    )
    assert movs.status_code == 200
    assert any(m["estado"] == "CONFIRMADO" for m in movs.json())

    # produced + rejected > planned → 400
    bad = api_client.post(
        f"{API}/ordenes-produccion/{op['id']}/items/{item_id}/cantidades",
        json={"cantidad_producida": "4", "cantidad_rechazada": "2"},
    )
    assert bad.status_code == 400, bad.text

    ok = api_client.post(
        f"{API}/ordenes-produccion/{op['id']}/items/{item_id}/cantidades",
        json={"cantidad_producida": "3", "cantidad_rechazada": "2"},
    )
    assert ok.status_code == 200, ok.text


def test_sin_doble_descuento_idempotente(api_client: TestClient) -> None:
    """Cada consumo genera exactamente un movimiento; stock cae una sola vez."""
    esc = _pedido_fabricado(api_client, sufijo="IDEM")
    op = _crear_op(api_client, esc, qty="2")
    item_id = op["items"][0]["id"]
    bodega = esc["bodega_id"]
    mat_id = esc["material"]["id"]
    api_client.post(f"{API}/ordenes-produccion/{op['id']}/iniciar")

    antes = _stock_material(api_client, bodega_id=bodega, material_id=mat_id)
    c = api_client.post(
        f"{API}/ordenes-produccion/{op['id']}/items/{item_id}/consumos",
        params={"bodega_id": bodega},
        json={"material_id": mat_id, "cantidad_consumida": "4.4"},
    )
    assert c.status_code == 201
    despues = _stock_material(api_client, bodega_id=bodega, material_id=mat_id)
    assert antes - despues == Decimal("4.4000")

    # Dos consumos distintos → dos descuentos (correcto)
    c2 = api_client.post(
        f"{API}/ordenes-produccion/{op['id']}/items/{item_id}/consumos",
        params={"bodega_id": bodega},
        json={"material_id": mat_id, "cantidad_consumida": "1"},
    )
    assert c2.status_code == 201
    final = _stock_material(api_client, bodega_id=bodega, material_id=mat_id)
    assert antes - final == Decimal("5.4000")

    # Movimientos PRODUCCION referenciados a consumos
    movs = api_client.get(
        f"{API}/movimientos-inventario",
        params={"tipo_movimiento": "PRODUCCION", "bodega_id": bodega},
    )
    assert movs.status_code == 200
    confirmados = [m for m in movs.json() if m["estado"] == "CONFIRMADO"]
    assert len(confirmados) >= 2


def test_estimado_vs_real(api_client: TestClient) -> None:
    esc = _pedido_fabricado(api_client, sufijo="COST")
    op = _crear_op(api_client, esc, qty="10")
    item_id = op["items"][0]["id"]
    bodega = esc["bodega_id"]

    # Al crear ya hay asientos ESTIMADO
    asientos_est = [
        a
        for a in op["items"][0]["asientos_costo"]
        if a["etapa_costo"] == "ESTIMADO"
    ]
    assert asientos_est
    # 10 * 20.50 = 205.00 estimado total
    total_est = sum(Decimal(str(a["costo_total"])) for a in asientos_est)
    assert total_est == Decimal("205.00")

    api_client.post(f"{API}/ordenes-produccion/{op['id']}/iniciar")
    api_client.post(
        f"{API}/ordenes-produccion/{op['id']}/items/{item_id}/consumos",
        params={"bodega_id": bodega},
        json={
            "material_id": esc["material"]["id"],
            "cantidad_consumida": "22",
        },
    )
    cat_mo = _categoria_costo(api_client, nombre="MO Cost", tipo="MANO_OBRA")
    api_client.post(
        f"{API}/ordenes-produccion/{op['id']}/items/{item_id}/asientos-costo",
        json={
            "categoria_costo_id": cat_mo["id"],
            "cantidad": "10",
            "costo_unitario": "10.00",
        },
    )
    api_client.post(
        f"{API}/ordenes-produccion/{op['id']}/items/{item_id}/cantidades",
        json={"cantidad_producida": "10", "cantidad_rechazada": "0"},
    )
    api_client.post(f"{API}/ordenes-produccion/{op['id']}/completar")

    cmp_ = api_client.get(
        f"{API}/ordenes-produccion/{op['id']}/comparacion-costos"
    ).json()
    assert Decimal(str(cmp_["costo_estimado_total"])) == Decimal("205.00")
    # real mat 110 + MO 100 = 210 (+ posibles otros si se registraran)
    assert Decimal(str(cmp_["items"][0]["costo_materiales_consumos"])) == Decimal(
        "110.00"
    )
    assert Decimal(str(cmp_["costo_real_total"])) >= Decimal("210.00")
    assert Decimal(str(cmp_["diferencia"])) == (
        Decimal(str(cmp_["costo_real_total"]))
        - Decimal(str(cmp_["costo_estimado_total"]))
    )


def test_op_requiere_pedido_y_fabricado(api_client: TestClient) -> None:
    inv = _catalogo_inventario(api_client, sufijo="REQ")
    mat = _material(api_client, inv, nombre="Mat REQ", costo="1", stock="10")
    cat_id = _categoria_producto(api_client, "Cat REQ")
    srv = _producto(api_client, cat_id, nombre="Srv REQ", tipo="SERVICIO")
    srv_v = _variante(
        api_client, srv["id"], sku="SRV-REQ", precio="100", control_stock=False
    )
    perfil = api_client.post(
        f"{API}/perfiles-costo-producto",
        json={
            "producto_id": srv["id"],
            "costo_mano_obra_por_unidad": "5",
            "activo": True,
        },
    )
    assert perfil.status_code == 201

    cli = _cliente(api_client, "Cli REQ")
    pedido = api_client.post(
        f"{API}/pedidos",
        json={
            "cliente_id": cli["id"],
            "items": [
                {
                    "producto_id": srv["id"],
                    "variante_id": srv_v["id"],
                    "cantidad": "1",
                }
            ],
        },
    ).json()
    api_client.post(
        f"{API}/pedidos/{pedido['id']}/estado",
        json={"estado_nuevo": "CONFIRMADO"},
    )

    bad = api_client.post(
        f"{API}/ordenes-produccion",
        json={
            "pedido_id": pedido["id"],
            "items": [{"item_pedido_id": pedido["items"][0]["id"]}],
        },
    )
    assert bad.status_code == 400, bad.text

    # Sin pedido_id en body → 422
    sin = api_client.post(
        f"{API}/ordenes-produccion",
        json={"items": [{"item_pedido_id": 1}]},
    )
    assert sin.status_code == 422

    # Cancelar OP planificada OK; con consumos bloqueado
    fab = _producto(api_client, cat_id, nombre="Fab REQ", tipo="FABRICADO")
    fab_v = _variante(api_client, fab["id"], sku="FAB-REQ", precio="200")
    _receta_y_perfil(
        api_client, producto_id=fab["id"], material_id=mat["id"], qty_mat="1", desperdicio="0"
    )
    ped2 = api_client.post(
        f"{API}/pedidos",
        json={
            "cliente_id": cli["id"],
            "items": [
                {
                    "producto_id": fab["id"],
                    "variante_id": fab_v["id"],
                    "cantidad": "2",
                }
            ],
        },
    ).json()
    api_client.post(
        f"{API}/pedidos/{ped2['id']}/estado",
        json={"estado_nuevo": "CONFIRMADO"},
    )
    op = api_client.post(
        f"{API}/ordenes-produccion",
        json={
            "pedido_id": ped2["id"],
            "items": [{"item_pedido_id": ped2["items"][0]["id"]}],
        },
    ).json()
    cancel = api_client.post(f"{API}/ordenes-produccion/{op['id']}/cancelar")
    assert cancel.status_code == 200
    assert cancel.json()["estado"] == "CANCELADA"
