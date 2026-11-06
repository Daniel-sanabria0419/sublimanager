"""Tests de integración Stage 5 — clientes, pedidos, diseños, anticipos."""

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


def _catalogo_inventario(client: TestClient) -> dict[str, int]:
    cat = client.post(
        f"{API}/categorias-material",
        json={"nombre": "Insumos Ped", "descripcion": "Base"},
    )
    assert cat.status_code == 201, cat.text
    uni = client.post(
        f"{API}/unidades-medida",
        json={"nombre": "Unidad Ped", "abreviatura": "up"},
    )
    assert uni.status_code == 201, uni.text
    bod = client.post(
        f"{API}/bodegas",
        json={"nombre": "Bodega Pedidos", "ubicacion": "Principal"},
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


def _existencias_material(
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


def _cliente(client: TestClient, nombre: str = "Acme Sublimación") -> dict:
    resp = client.post(
        f"{API}/clientes",
        json={
            "nombre": nombre,
            "identificacion": "900123",
            "telefono": "3001112233",
            "email": "acme@example.com",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _categoria_producto(client: TestClient, nombre: str = "Cat Ped") -> int:
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
    talla: str = "M",
    color: str = "Blanco",
    control_stock: bool = True,
) -> dict:
    resp = client.post(
        f"{API}/variantes-producto",
        json={
            "producto_id": producto_id,
            "sku": sku,
            "talla": talla,
            "color": color,
            "precio_venta": precio,
            "control_stock": control_stock,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _receta_y_perfil_fabricado(
    client: TestClient,
    *,
    producto_id: int,
    material_id: int,
    qty_mat: str = "1",
    desperdicio: str = "0",
    mano_obra: str = "10.00",
) -> None:
    receta = client.post(
        f"{API}/recetas-producto",
        json={
            "producto_id": producto_id,
            "nombre": "BOM pedido",
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
            "costo_electricidad_por_unidad": "0",
            "costo_depreciacion_por_unidad": "0",
            "costo_otros_por_unidad": "0",
            "activo": True,
        },
    )
    assert perfil.status_code == 201, perfil.text


def _perfil_servicio(
    client: TestClient, producto_id: int, *, mano: str, otros: str
) -> None:
    perfil = client.post(
        f"{API}/perfiles-costo-producto",
        json={
            "producto_id": producto_id,
            "costo_mano_obra_por_unidad": mano,
            "costo_otros_por_unidad": otros,
            "activo": True,
        },
    )
    assert perfil.status_code == 201, perfil.text


def _metodo_y_cuenta(client: TestClient) -> tuple[int, int]:
    m = client.post(f"{API}/metodos-pago", json={"nombre": "Transferencia"})
    assert m.status_code == 201, m.text
    c = client.post(
        f"{API}/cuentas-caja",
        json={"nombre": "Caja Principal", "tipo_cuenta": "EFECTIVO"},
    )
    assert c.status_code == 201, c.text
    return m.json()["id"], c.json()["id"]


def _escenario_multiproducto(client: TestClient) -> dict:
    """FABRICADO (con receta) + SERVICIO + REVENTA listos para un pedido."""
    inv = _catalogo_inventario(client)
    mat = _material(client, inv, nombre="Vinilo", costo="5.00", stock="200")
    cat_id = _categoria_producto(client, "Mix Pedidos")

    fab = _producto(client, cat_id, nombre="Camiseta subli", tipo="FABRICADO")
    fab_v = _variante(
        client, fab["id"], sku="CAM-M-BL-PED", precio="40000.00", talla="M"
    )
    _receta_y_perfil_fabricado(
        client,
        producto_id=fab["id"],
        material_id=mat["id"],
        qty_mat="2",
        desperdicio="10",
        mano_obra="8.00",
    )
    # costo mat = 2*5*1.10 = 11; + mano 8 = 19.00

    srv = _producto(client, cat_id, nombre="Diseño logo", tipo="SERVICIO")
    srv_v = _variante(
        client,
        srv["id"],
        sku="DIS-LOGO-PED",
        precio="50000.00",
        control_stock=False,
    )
    _perfil_servicio(client, srv["id"], mano="20.00", otros="5.00")
    # costo = 25.00

    rev = _producto(client, cat_id, nombre="Gorra stock", tipo="REVENTA")
    rev_v = _variante(
        client, rev["id"], sku="GOR-NE-PED", precio="15000.00", color="Negro"
    )

    cliente = _cliente(client)
    return {
        "inv": inv,
        "mat": mat,
        "cliente": cliente,
        "fab": fab,
        "fab_v": fab_v,
        "srv": srv,
        "srv_v": srv_v,
        "rev": rev,
        "rev_v": rev_v,
        "costo_fab_esperado": Decimal("19.00"),
        "costo_srv_esperado": Decimal("25.00"),
        "costo_rev_esperado": Decimal("0.00"),
    }


# ---------------------------------------------------------------------------
# Clientes CRUD
# ---------------------------------------------------------------------------


def test_clientes_crud(api_client: TestClient) -> None:
    creado = _cliente(api_client, "Cliente Uno")
    assert creado["nombre"] == "Cliente Uno"
    assert creado["activo"] is True

    lista = api_client.get(f"{API}/clientes", params={"activo": True})
    assert lista.status_code == 200
    assert any(c["id"] == creado["id"] for c in lista.json())

    patch = api_client.patch(
        f"{API}/clientes/{creado['id']}",
        json={"telefono": "3119998877", "notas": "VIP"},
    )
    assert patch.status_code == 200
    assert patch.json()["telefono"] == "3119998877"

    baja = api_client.delete(f"{API}/clientes/{creado['id']}")
    assert baja.status_code == 200
    obt = api_client.get(f"{API}/clientes/{creado['id']}")
    assert obt.json()["activo"] is False


# ---------------------------------------------------------------------------
# Pedido multi-producto + variantes + descuento monto + costos estimados
# ---------------------------------------------------------------------------


def test_pedido_multiproducto_descuento_y_costos(api_client: TestClient) -> None:
    esc = _escenario_multiproducto(api_client)

    # 2 camisetas * 40000 = 80000; 1 diseño * 50000; 3 gorras * 15000 = 45000
    # subtotal = 175000; descuento monto 5000; total = 170000
    pedido = api_client.post(
        f"{API}/pedidos",
        json={
            "cliente_id": esc["cliente"]["id"],
            "numero_pedido": "PED-TEST-001",
            "descuento": "5000.00",
            "notas": "Pedido mixto Stage 5",
            "items": [
                {
                    "producto_id": esc["fab"]["id"],
                    "variante_id": esc["fab_v"]["id"],
                    "cantidad": "2",
                },
                {
                    "producto_id": esc["srv"]["id"],
                    "variante_id": esc["srv_v"]["id"],
                    "cantidad": "1",
                    "descripcion": "Logo full color",
                },
                {
                    "producto_id": esc["rev"]["id"],
                    "variante_id": esc["rev_v"]["id"],
                    "cantidad": "3",
                },
            ],
        },
    )
    assert pedido.status_code == 201, pedido.text
    body = pedido.json()
    assert body["numero_pedido"] == "PED-TEST-001"
    assert body["estado"] == "PENDIENTE"
    assert len(body["items"]) == 3
    assert Decimal(str(body["subtotal"])) == Decimal("175000.00")
    assert Decimal(str(body["descuento"])) == Decimal("5000.00")
    assert Decimal(str(body["total"])) == Decimal("170000.00")
    assert Decimal(str(body["saldo_pendiente"])) == Decimal("170000.00")
    assert Decimal(str(body["total_pagado"])) == Decimal("0.00")

    por_prod = {i["producto_id"]: i for i in body["items"]}
    fab_item = por_prod[esc["fab"]["id"]]
    srv_item = por_prod[esc["srv"]["id"]]
    rev_item = por_prod[esc["rev"]["id"]]

    assert Decimal(str(fab_item["precio_venta_unitario"])) == Decimal("40000.00")
    assert Decimal(str(fab_item["subtotal"])) == Decimal("80000.00")
    assert Decimal(str(fab_item["costo_unitario_estimado"])) == esc[
        "costo_fab_esperado"
    ]

    assert Decimal(str(srv_item["costo_unitario_estimado"])) == esc[
        "costo_srv_esperado"
    ]
    assert Decimal(str(rev_item["costo_unitario_estimado"])) == esc[
        "costo_rev_esperado"
    ]
    assert Decimal(str(rev_item["subtotal"])) == Decimal("45000.00")

    # Historial inicial
    hist = api_client.get(f"{API}/pedidos/{body['id']}/historial-estados")
    assert hist.status_code == 200
    assert len(hist.json()) == 1
    assert hist.json()[0]["estado_anterior"] is None
    assert hist.json()[0]["estado_nuevo"] == "PENDIENTE"


def test_descuento_no_supera_subtotal(api_client: TestClient) -> None:
    esc = _escenario_multiproducto(api_client)
    bad = api_client.post(
        f"{API}/pedidos",
        json={
            "cliente_id": esc["cliente"]["id"],
            "descuento": "999999.00",
            "items": [
                {
                    "producto_id": esc["srv"]["id"],
                    "variante_id": esc["srv_v"]["id"],
                    "cantidad": "1",
                }
            ],
        },
    )
    assert bad.status_code == 400, bad.text


# ---------------------------------------------------------------------------
# Crear pedido NO descuenta inventario de materiales
# ---------------------------------------------------------------------------


def test_crear_pedido_no_descuenta_inventario(api_client: TestClient) -> None:
    esc = _escenario_multiproducto(api_client)
    stock_antes = _existencias_material(
        api_client,
        bodega_id=esc["inv"]["bodega_id"],
        material_id=esc["mat"]["id"],
    )
    assert stock_antes == Decimal("200.0000")

    pedido = api_client.post(
        f"{API}/pedidos",
        json={
            "cliente_id": esc["cliente"]["id"],
            "items": [
                {
                    "producto_id": esc["fab"]["id"],
                    "variante_id": esc["fab_v"]["id"],
                    "cantidad": "10",
                }
            ],
        },
    )
    assert pedido.status_code == 201, pedido.text

    stock_despues = _existencias_material(
        api_client,
        bodega_id=esc["inv"]["bodega_id"],
        material_id=esc["mat"]["id"],
    )
    assert stock_despues == stock_antes

    # Tampoco debe haber movimientos referenciando el pedido
    movs = api_client.get(
        f"{API}/movimientos-inventario",
        params={"tipo_movimiento": "VENTA"},
    )
    assert movs.status_code == 200
    assert all(
        m.get("referencia_id") != pedido.json()["id"] for m in movs.json()
    )


# ---------------------------------------------------------------------------
# Anticipos / saldo pendiente
# ---------------------------------------------------------------------------


def test_anticipos_y_saldo_pendiente(api_client: TestClient) -> None:
    esc = _escenario_multiproducto(api_client)
    metodo_id, cuenta_id = _metodo_y_cuenta(api_client)

    pedido = api_client.post(
        f"{API}/pedidos",
        json={
            "cliente_id": esc["cliente"]["id"],
            "descuento": "0",
            "items": [
                {
                    "producto_id": esc["srv"]["id"],
                    "variante_id": esc["srv_v"]["id"],
                    "cantidad": "1",
                }
            ],
        },
    )
    assert pedido.status_code == 201, pedido.text
    pid = pedido.json()["id"]
    total = Decimal(str(pedido.json()["total"]))
    assert total == Decimal("50000.00")

    anticipo = api_client.post(
        f"{API}/pagos",
        json={
            "pedido_id": pid,
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "20000.00",
            "referencia": "ANT-1",
            "confirmar": True,
        },
    )
    assert anticipo.status_code == 201, anticipo.text
    assert anticipo.json()["estado"] == "CONFIRMADO"

    saldo = api_client.get(f"{API}/pedidos/{pid}/saldo")
    assert saldo.status_code == 200
    assert Decimal(saldo.json()["total_pagado"]) == Decimal("20000.00")
    assert Decimal(saldo.json()["saldo_pendiente"]) == Decimal("30000.00")

    det = api_client.get(f"{API}/pedidos/{pid}")
    assert Decimal(str(det.json()["saldo_pendiente"])) == Decimal("30000.00")

    # Pago PENDIENTE no reduce saldo
    pend = api_client.post(
        f"{API}/pagos",
        json={
            "pedido_id": pid,
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "5000.00",
            "confirmar": False,
        },
    )
    assert pend.status_code == 201
    assert pend.json()["estado"] == "PENDIENTE"
    saldo2 = api_client.get(f"{API}/pedidos/{pid}/saldo")
    assert Decimal(saldo2.json()["saldo_pendiente"]) == Decimal("30000.00")

    conf = api_client.post(f"{API}/pagos/{pend.json()['id']}/confirmar")
    assert conf.status_code == 200
    assert conf.json()["estado"] == "CONFIRMADO"
    saldo3 = api_client.get(f"{API}/pedidos/{pid}/saldo")
    assert Decimal(saldo3.json()["saldo_pendiente"]) == Decimal("25000.00")

    # No superar saldo
    exceso = api_client.post(
        f"{API}/pagos",
        json={
            "pedido_id": pid,
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "25000.01",
            "confirmar": True,
        },
    )
    assert exceso.status_code == 409, exceso.text


# ---------------------------------------------------------------------------
# Cancelación + historial de estados + diseños
# ---------------------------------------------------------------------------


def test_cancelacion_historial_y_disenos(api_client: TestClient) -> None:
    esc = _escenario_multiproducto(api_client)
    pedido = api_client.post(
        f"{API}/pedidos",
        json={
            "cliente_id": esc["cliente"]["id"],
            "items": [
                {
                    "producto_id": esc["fab"]["id"],
                    "variante_id": esc["fab_v"]["id"],
                    "cantidad": "1",
                }
            ],
        },
    )
    assert pedido.status_code == 201, pedido.text
    pid = pedido.json()["id"]
    item_id = pedido.json()["items"][0]["id"]

    # Diseño: solo ruta
    diseno = api_client.post(
        f"{API}/pedidos/{pid}/disenos",
        json={
            "item_pedido_id": item_id,
            "ruta_archivo": "/data/disenos/pedido1/v1.png",
            "estado_aprobacion": "BORRADOR",
            "notas": "Boceto inicial",
        },
    )
    assert diseno.status_code == 201, diseno.text
    assert diseno.json()["version"] == 1
    assert diseno.json()["ruta_archivo"] == "/data/disenos/pedido1/v1.png"
    assert diseno.json()["estado_aprobacion"] == "BORRADOR"

    v2 = api_client.post(
        f"{API}/pedidos/{pid}/disenos",
        json={
            "item_pedido_id": item_id,
            "ruta_archivo": "/data/disenos/pedido1/v2.png",
            "estado_aprobacion": "PENDIENTE_APROBACION",
        },
    )
    assert v2.status_code == 201
    assert v2.json()["version"] == 2

    apr = api_client.patch(
        f"{API}/pedidos/disenos/{v2.json()['id']}",
        json={"estado_aprobacion": "APROBADO"},
    )
    assert apr.status_code == 200
    assert apr.json()["estado_aprobacion"] == "APROBADO"

    # Flujo de estados
    conf = api_client.post(
        f"{API}/pedidos/{pid}/estado",
        json={"estado_nuevo": "CONFIRMADO", "notas": "Cliente OK"},
    )
    assert conf.status_code == 200
    assert conf.json()["estado"] == "CONFIRMADO"

    # Transición inválida
    bad = api_client.post(
        f"{API}/pedidos/{pid}/estado",
        json={"estado_nuevo": "ENTREGADO"},
    )
    assert bad.status_code == 409, bad.text

    cancel = api_client.post(f"{API}/pedidos/{pid}/cancelar")
    assert cancel.status_code == 200
    assert cancel.json()["estado"] == "CANCELADO"

    hist = api_client.get(f"{API}/pedidos/{pid}/historial-estados")
    assert hist.status_code == 200
    estados = [(h["estado_anterior"], h["estado_nuevo"]) for h in hist.json()]
    assert (None, "PENDIENTE") in estados
    assert ("PENDIENTE", "CONFIRMADO") in estados
    assert ("CONFIRMADO", "CANCELADO") in estados

    # No se puede cancelar de nuevo ni editar
    re = api_client.post(f"{API}/pedidos/{pid}/cancelar")
    assert re.status_code == 409
    edit = api_client.patch(
        f"{API}/pedidos/{pid}", json={"notas": "después de cancelar"}
    )
    assert edit.status_code == 409


def test_numero_pedido_unico(api_client: TestClient) -> None:
    esc = _escenario_multiproducto(api_client)
    payload = {
        "cliente_id": esc["cliente"]["id"],
        "numero_pedido": "PED-DUP-9",
        "items": [
            {
                "producto_id": esc["srv"]["id"],
                "variante_id": esc["srv_v"]["id"],
                "cantidad": "1",
            }
        ],
    }
    first = api_client.post(f"{API}/pedidos", json=payload)
    assert first.status_code == 201, first.text
    second = api_client.post(f"{API}/pedidos", json=payload)
    assert second.status_code == 409, second.text
