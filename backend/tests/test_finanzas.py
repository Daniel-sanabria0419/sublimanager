"""Tests de integración Stage 7 — Finanzas (pagos, gastos, caja, CxC/CxP, resumen)."""

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


def _metodo_y_cuenta(
    client: TestClient, *, sufijo: str = ""
) -> tuple[int, int]:
    m = client.post(
        f"{API}/metodos-pago",
        json={"nombre": f"Efectivo{sufijo}"},
    )
    assert m.status_code == 201, m.text
    c = client.post(
        f"{API}/cuentas-caja",
        json={
            "nombre": f"Caja{sufijo}",
            "tipo_cuenta": "EFECTIVO",
        },
    )
    assert c.status_code == 201, c.text
    return m.json()["id"], c.json()["id"]


def _cliente_servicio_pedido(
    client: TestClient, *, precio: str = "100000.00", nombre: str = "Cli Fin"
) -> dict:
    cli = client.post(
        f"{API}/clientes",
        json={"nombre": nombre},
    )
    assert cli.status_code == 201, cli.text
    cat = client.post(
        f"{API}/categorias-producto",
        json={"nombre": f"Cat-{nombre}"},
    )
    assert cat.status_code == 201, cat.text
    prod = client.post(
        f"{API}/productos",
        json={
            "categoria_id": cat.json()["id"],
            "nombre": f"Serv-{nombre}",
            "tipo_producto": "SERVICIO",
        },
    )
    assert prod.status_code == 201, prod.text
    var = client.post(
        f"{API}/variantes-producto",
        json={
            "producto_id": prod.json()["id"],
            "sku": f"SKU-{nombre.replace(' ', '')[:20]}",
            "precio_venta": precio,
            "control_stock": False,
        },
    )
    assert var.status_code == 201, var.text
    # Perfil mínimo para SERVICIO
    perfil = client.post(
        f"{API}/perfiles-costo-producto",
        json={
            "producto_id": prod.json()["id"],
            "costo_mano_obra_por_unidad": "10.00",
            "costo_otros_por_unidad": "0",
            "activo": True,
        },
    )
    assert perfil.status_code == 201, perfil.text

    pedido = client.post(
        f"{API}/pedidos",
        json={
            "cliente_id": cli.json()["id"],
            "descuento": "0",
            "items": [
                {
                    "producto_id": prod.json()["id"],
                    "variante_id": var.json()["id"],
                    "cantidad": "1",
                }
            ],
        },
    )
    assert pedido.status_code == 201, pedido.text
    return {
        "cliente": cli.json(),
        "producto": prod.json(),
        "variante": var.json(),
        "pedido": pedido.json(),
    }


def _entregar_pedido(client: TestClient, pedido_id: int) -> None:
    """PENDIENTE → CONFIRMADO → LISTO → ENTREGADO (ruta corta SERVICIO)."""
    for estado in ("CONFIRMADO", "LISTO", "ENTREGADO"):
        r = client.post(
            f"{API}/pedidos/{pedido_id}/estado",
            json={"estado_nuevo": estado},
        )
        assert r.status_code == 200, r.text


def _bootstrap_compra(
    client: TestClient, *, total_unitario: str = "50.00", qty: str = "10"
) -> dict:
    cat = client.post(
        f"{API}/categorias-material",
        json={"nombre": "Mat Fin"},
    )
    assert cat.status_code == 201, cat.text
    uni = client.post(
        f"{API}/unidades-medida",
        json={"nombre": "Unidad Fin", "abreviatura": "uf"},
    )
    assert uni.status_code == 201, uni.text
    bod = client.post(
        f"{API}/bodegas",
        json={"nombre": "Bod Fin"},
    )
    assert bod.status_code == 201, bod.text
    mat = client.post(
        f"{API}/materiales",
        json={
            "categoria_id": cat.json()["id"],
            "unidad_id": uni.json()["id"],
            "nombre": "Vinilo Fin",
            "stock_minimo": "1",
        },
    )
    assert mat.status_code == 201, mat.text
    prov = client.post(
        f"{API}/proveedores",
        json={"nombre": "Prov Fin"},
    )
    assert prov.status_code == 201, prov.text
    compra = client.post(
        f"{API}/compras",
        json={
            "proveedor_id": prov.json()["id"],
            "items": [
                {
                    "material_id": mat.json()["id"],
                    "cantidad": qty,
                    "costo_unitario": total_unitario,
                }
            ],
        },
    )
    assert compra.status_code == 201, compra.text
    # Recibir para dejar compra activa (no CANCELADA)
    recv = client.post(
        f"{API}/compras/{compra.json()['id']}/recibir",
        json={
            "bodega_id": bod.json()["id"],
            "items": [
                {
                    "item_compra_id": compra.json()["items"][0]["id"],
                    "cantidad": qty,
                }
            ],
        },
    )
    assert recv.status_code == 200, recv.text
    return {
        "compra": recv.json(),
        "proveedor_id": prov.json()["id"],
        "bodega_id": bod.json()["id"],
        "material_id": mat.json()["id"],
    }


# ---------------------------------------------------------------------------
# CRUD métodos / cuentas
# ---------------------------------------------------------------------------


def test_crud_metodos_y_cuentas(api_client: TestClient) -> None:
    m = api_client.post(
        f"{API}/metodos-pago", json={"nombre": "Nequi CRUD"}
    )
    assert m.status_code == 201
    mid = m.json()["id"]
    patch = api_client.patch(
        f"{API}/metodos-pago/{mid}", json={"nombre": "Nequi Edit"}
    )
    assert patch.status_code == 200
    assert patch.json()["nombre"] == "Nequi Edit"
    baja = api_client.delete(f"{API}/metodos-pago/{mid}")
    assert baja.status_code == 204
    assert api_client.get(f"{API}/metodos-pago/{mid}").json()["activo"] is False

    c = api_client.post(
        f"{API}/cuentas-caja",
        json={"nombre": "Banco CRUD", "tipo_cuenta": "BANCO"},
    )
    assert c.status_code == 201
    cid = c.json()["id"]
    patch_c = api_client.patch(
        f"{API}/cuentas-caja/{cid}",
        json={"tipo_cuenta": "BILLETERA_DIGITAL"},
    )
    assert patch_c.status_code == 200
    assert patch_c.json()["tipo_cuenta"] == "BILLETERA_DIGITAL"


# ---------------------------------------------------------------------------
# Pagos de clientes: anticipos, parciales, completo, anulación, idempotencia
# ---------------------------------------------------------------------------


def test_pagos_parciales_completo_y_sin_sobrepaid(api_client: TestClient) -> None:
    esc = _cliente_servicio_pedido(api_client, precio="100000.00", nombre="PagoPar")
    metodo_id, cuenta_id = _metodo_y_cuenta(api_client, sufijo="-par")
    pid = esc["pedido"]["id"]

    a1 = api_client.post(
        f"{API}/pagos",
        json={
            "pedido_id": pid,
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "40000.00",
            "confirmar": True,
        },
    )
    assert a1.status_code == 201
    assert a1.json()["estado"] == "CONFIRMADO"

    a2 = api_client.post(
        f"{API}/pagos",
        json={
            "pedido_id": pid,
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "60000.00",
            "confirmar": True,
        },
    )
    assert a2.status_code == 201

    saldo = api_client.get(f"{API}/pedidos/{pid}/saldo")
    assert Decimal(saldo.json()["saldo_pendiente"]) == Decimal("0")

    exceso = api_client.post(
        f"{API}/pagos",
        json={
            "pedido_id": pid,
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "0.01",
            "confirmar": True,
        },
    )
    assert exceso.status_code == 409

    movs = api_client.get(
        f"{API}/movimientos-caja", params={"cuenta_caja_id": cuenta_id}
    )
    assert movs.status_code == 200
    assert len(movs.json()) == 2
    assert all(m["tipo_movimiento"] == "ENTRADA" for m in movs.json())
    assert all(m["pago_id"] is not None for m in movs.json())


def test_confirmacion_idempotente_y_anulacion_confirmado(
    api_client: TestClient,
) -> None:
    esc = _cliente_servicio_pedido(api_client, precio="50000.00", nombre="PagoIdem")
    metodo_id, cuenta_id = _metodo_y_cuenta(api_client, sufijo="-idem")
    pid = esc["pedido"]["id"]

    pend = api_client.post(
        f"{API}/pagos",
        json={
            "pedido_id": pid,
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "20000.00",
            "confirmar": False,
        },
    )
    assert pend.status_code == 201
    pago_id = pend.json()["id"]

    c1 = api_client.post(f"{API}/pagos/{pago_id}/confirmar")
    assert c1.status_code == 200
    assert c1.json()["estado"] == "CONFIRMADO"

    # Segunda confirmación: idempotente, sin duplicar movimiento
    c2 = api_client.post(f"{API}/pagos/{pago_id}/confirmar")
    assert c2.status_code == 200
    assert c2.json()["estado"] == "CONFIRMADO"

    movs = api_client.get(
        f"{API}/movimientos-caja",
        params={"cuenta_caja_id": cuenta_id},
    )
    assert len([m for m in movs.json() if m["pago_id"] == pago_id]) == 1

    saldo_antes = api_client.get(f"{API}/cuentas-caja/{cuenta_id}/saldo")
    assert Decimal(str(saldo_antes.json()["saldo"])) == Decimal("20000.00")

    anula = api_client.post(f"{API}/pagos/{pago_id}/anular")
    assert anula.status_code == 200
    assert anula.json()["estado"] == "ANULADO"

    movs2 = api_client.get(
        f"{API}/movimientos-caja",
        params={"cuenta_caja_id": cuenta_id},
    )
    assert [m for m in movs2.json() if m["pago_id"] == pago_id] == []

    saldo_despues = api_client.get(f"{API}/cuentas-caja/{cuenta_id}/saldo")
    assert Decimal(str(saldo_despues.json()["saldo"])) == Decimal("0")

    saldo_ped = api_client.get(f"{API}/pedidos/{pid}/saldo")
    assert Decimal(saldo_ped.json()["saldo_pendiente"]) == Decimal("50000.00")


# ---------------------------------------------------------------------------
# Gastos + pagos parciales + estado_pago
# ---------------------------------------------------------------------------


def test_gastos_parciales_y_estado_pago(api_client: TestClient) -> None:
    metodo_id, cuenta_id = _metodo_y_cuenta(api_client, sufijo="-gas")
    # Sembrar caja con un cobro previo
    esc = _cliente_servicio_pedido(api_client, precio="200000.00", nombre="GastoSeed")
    api_client.post(
        f"{API}/pagos",
        json={
            "pedido_id": esc["pedido"]["id"],
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "200000.00",
            "confirmar": True,
        },
    )

    cat = api_client.post(
        f"{API}/categorias-gasto",
        json={"nombre": "Arriendo", "descripcion": "Local"},
    )
    assert cat.status_code == 201, cat.text

    gasto = api_client.post(
        f"{API}/gastos",
        json={
            "categoria_id": cat.json()["id"],
            "descripcion": "Arriendo marzo",
            "monto": "100000.00",
        },
    )
    assert gasto.status_code == 201, gasto.text
    gid = gasto.json()["id"]
    assert gasto.json()["estado_pago"] == "NO_PAGADO"
    assert Decimal(str(gasto.json()["saldo_pendiente"])) == Decimal("100000.00")

    p1 = api_client.post(
        f"{API}/pagos-gasto",
        json={
            "gasto_id": gid,
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "40000.00",
            "confirmar": True,
        },
    )
    assert p1.status_code == 201, p1.text
    det = api_client.get(f"{API}/gastos/{gid}")
    assert det.json()["estado_pago"] == "PARCIAL"
    assert Decimal(str(det.json()["saldo_pendiente"])) == Decimal("60000.00")

    p2 = api_client.post(
        f"{API}/pagos-gasto",
        json={
            "gasto_id": gid,
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "60000.00",
            "confirmar": True,
        },
    )
    assert p2.status_code == 201
    det2 = api_client.get(f"{API}/gastos/{gid}")
    assert det2.json()["estado_pago"] == "PAGADO"
    assert Decimal(str(det2.json()["saldo_pendiente"])) == Decimal("0")

    exceso = api_client.post(
        f"{API}/pagos-gasto",
        json={
            "gasto_id": gid,
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "1.00",
            "confirmar": True,
        },
    )
    assert exceso.status_code == 409

    movs = api_client.get(
        f"{API}/movimientos-caja",
        params={"tipo_movimiento": "SALIDA", "cuenta_caja_id": cuenta_id},
    )
    assert len(movs.json()) == 2
    assert all(m["pago_gasto_id"] is not None for m in movs.json())


def test_gasto_pendiente_en_listado_y_anulacion_pago(
    api_client: TestClient,
) -> None:
    metodo_id, cuenta_id = _metodo_y_cuenta(api_client, sufijo="-pend")
    esc = _cliente_servicio_pedido(api_client, precio="50000.00", nombre="GastoPend")
    api_client.post(
        f"{API}/pagos",
        json={
            "pedido_id": esc["pedido"]["id"],
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "50000.00",
            "confirmar": True,
        },
    )
    cat = api_client.post(
        f"{API}/categorias-gasto", json={"nombre": "Servicios"}
    )
    assert cat.status_code == 201
    gasto = api_client.post(
        f"{API}/gastos",
        json={
            "categoria_id": cat.json()["id"],
            "descripcion": "Internet",
            "monto": "80000.00",
        },
    )
    gid = gasto.json()["id"]
    pago = api_client.post(
        f"{API}/pagos-gasto",
        json={
            "gasto_id": gid,
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "30000.00",
            "confirmar": True,
        },
    )
    assert pago.status_code == 201
    pendiente = api_client.get(
        f"{API}/gastos", params={"estado_pago": "PARCIAL"}
    )
    assert any(g["id"] == gid for g in pendiente.json())

    anula = api_client.post(f"{API}/pagos-gasto/{pago.json()['id']}/anular")
    assert anula.status_code == 200
    assert anula.json()["estado"] == "ANULADO"
    det = api_client.get(f"{API}/gastos/{gid}")
    assert det.json()["estado_pago"] == "NO_PAGADO"


# ---------------------------------------------------------------------------
# Pagos a proveedores
# ---------------------------------------------------------------------------


def test_pagos_proveedor_parciales_y_saldo(api_client: TestClient) -> None:
    metodo_id, cuenta_id = _metodo_y_cuenta(api_client, sufijo="-prov")
    # Sembrar caja
    esc = _cliente_servicio_pedido(api_client, precio="1000000.00", nombre="ProvSeed")
    api_client.post(
        f"{API}/pagos",
        json={
            "pedido_id": esc["pedido"]["id"],
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "1000000.00",
            "confirmar": True,
        },
    )
    data = _bootstrap_compra(api_client, total_unitario="50.00", qty="10")
    compra_id = data["compra"]["id"]
    assert Decimal(str(data["compra"]["total"])) == Decimal("500.00")

    saldo0 = api_client.get(f"{API}/pagos-proveedor/saldo/{compra_id}")
    assert Decimal(str(saldo0.json()["saldo_pendiente"])) == Decimal("500.00")

    p1 = api_client.post(
        f"{API}/pagos-proveedor",
        json={
            "compra_id": compra_id,
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "200.00",
            "confirmar": True,
        },
    )
    assert p1.status_code == 201, p1.text

    saldo1 = api_client.get(f"{API}/pagos-proveedor/saldo/{compra_id}")
    assert Decimal(str(saldo1.json()["saldo_pendiente"])) == Decimal("300.00")

    p2 = api_client.post(
        f"{API}/pagos-proveedor",
        json={
            "compra_id": compra_id,
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "300.00",
            "confirmar": False,
        },
    )
    assert p2.status_code == 201
    conf = api_client.post(f"{API}/pagos-proveedor/{p2.json()['id']}/confirmar")
    assert conf.status_code == 200
    # Idempotente
    conf2 = api_client.post(f"{API}/pagos-proveedor/{p2.json()['id']}/confirmar")
    assert conf2.status_code == 200

    saldo2 = api_client.get(f"{API}/pagos-proveedor/saldo/{compra_id}")
    assert Decimal(str(saldo2.json()["saldo_pendiente"])) == Decimal("0")

    movs = api_client.get(
        f"{API}/movimientos-caja",
        params={"tipo_movimiento": "SALIDA"},
    )
    prov_movs = [m for m in movs.json() if m["pago_proveedor_id"] is not None]
    assert len(prov_movs) == 2


# ---------------------------------------------------------------------------
# CxC / CxP / resumen / no doble conteo compras como gasto
# ---------------------------------------------------------------------------


def test_cxc_cxp_resumen_y_compras_no_son_gastos(api_client: TestClient) -> None:
    metodo_id, cuenta_id = _metodo_y_cuenta(api_client, sufijo="-res")

    esc = _cliente_servicio_pedido(
        api_client, precio="100000.00", nombre="ResumenFin"
    )
    pid = esc["pedido"]["id"]
    _entregar_pedido(api_client, pid)

    # Anticipo parcial → CxC = 60000; ventas reconocidas = 100000
    api_client.post(
        f"{API}/pagos",
        json={
            "pedido_id": pid,
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "40000.00",
            "confirmar": True,
        },
    )

    cxc = api_client.get(f"{API}/finanzas/cuentas-por-cobrar")
    assert cxc.status_code == 200
    fila = next(f for f in cxc.json() if f["pedido_id"] == pid)
    assert Decimal(str(fila["saldo_pendiente"])) == Decimal("60000.00")

    # Compra inventario + pago parcial → CxP; NO aumenta gastos_operativos
    data = _bootstrap_compra(api_client, total_unitario="100.00", qty="5")
    compra_id = data["compra"]["id"]  # total 500
    api_client.post(
        f"{API}/pagos-proveedor",
        json={
            "compra_id": compra_id,
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "200.00",
            "confirmar": True,
        },
    )
    cxp = api_client.get(f"{API}/finanzas/cuentas-por-pagar")
    assert cxp.status_code == 200
    fila_p = next(f for f in cxp.json() if f["compra_id"] == compra_id)
    assert Decimal(str(fila_p["saldo_pendiente"])) == Decimal("300.00")

    # Gasto operativo real
    cat = api_client.post(
        f"{API}/categorias-gasto", json={"nombre": "Publicidad"}
    )
    assert cat.status_code == 201
    api_client.post(
        f"{API}/gastos",
        json={
            "categoria_id": cat.json()["id"],
            "descripcion": "Ads",
            "monto": "15000.00",
        },
    )

    resumen = api_client.get(f"{API}/finanzas/resumen")
    assert resumen.status_code == 200, resumen.text
    body = resumen.json()
    assert Decimal(str(body["ventas_reconocidas"])) == Decimal("100000.00")
    assert Decimal(str(body["dinero_recibido"])) == Decimal("40000.00")
    assert Decimal(str(body["cuentas_por_cobrar"])) == Decimal("60000.00")
    assert Decimal(str(body["gastos_operativos"])) == Decimal("15000.00")
    assert Decimal(str(body["compras_inventario_pagadas"])) == Decimal("200.00")
    assert Decimal(str(body["cuentas_por_pagar"])) == Decimal("300.00")
    # Compras NO se suman a gastos operativos
    assert Decimal(str(body["gastos_operativos"])) != Decimal(
        str(body["compras_inventario_pagadas"])
    ) + Decimal("15000.00")
    assert Decimal(str(body["utilidad_bruta"])) == Decimal(
        str(body["ventas_reconocidas"])
    ) - Decimal(str(body["costos_produccion"]))
    assert Decimal(str(body["utilidad_operativa"])) == Decimal(
        str(body["utilidad_bruta"])
    ) - Decimal(str(body["gastos_operativos"]))


def test_electricidad_ligada_a_op_no_doble_conteo_en_gastos(
    api_client: TestClient,
) -> None:
    """Si un gasto está en asientos_costo.gasto_id, el resumen lo excluye de gastos_op."""
    cat_g = api_client.post(
        f"{API}/categorias-gasto", json={"nombre": "Energia"}
    )
    assert cat_g.status_code == 201
    gasto = api_client.post(
        f"{API}/gastos",
        json={
            "categoria_id": cat_g.json()["id"],
            "descripcion": "Factura electricidad",
            "monto": "25000.00",
        },
    )
    assert gasto.status_code == 201
    gid = gasto.json()["id"]

    gasto2 = api_client.post(
        f"{API}/gastos",
        json={
            "categoria_id": cat_g.json()["id"],
            "descripcion": "Aseo oficina",
            "monto": "5000.00",
        },
    )
    assert gasto2.status_code == 201

    resumen = api_client.get(f"{API}/finanzas/resumen")
    assert Decimal(str(resumen.json()["gastos_operativos"])) == Decimal("30000.00")

    inv_cat = api_client.post(
        f"{API}/categorias-material", json={"nombre": "Mat Elec"}
    )
    uni = api_client.post(
        f"{API}/unidades-medida",
        json={"nombre": "u-elec", "abreviatura": "ue"},
    )
    bod = api_client.post(f"{API}/bodegas", json={"nombre": "Bod Elec"})
    mat = api_client.post(
        f"{API}/materiales",
        json={
            "categoria_id": inv_cat.json()["id"],
            "unidad_id": uni.json()["id"],
            "nombre": "Tinta Elec",
            "stock_minimo": "1",
            "stock_inicial": "100",
            "bodega_id": bod.json()["id"],
            "costo_unitario_inicial": "2.00",
        },
    )
    cat_p = api_client.post(
        f"{API}/categorias-producto", json={"nombre": "Cat Elec"}
    )
    prod = api_client.post(
        f"{API}/productos",
        json={
            "categoria_id": cat_p.json()["id"],
            "nombre": "Prod Elec",
            "tipo_producto": "FABRICADO",
        },
    )
    var = api_client.post(
        f"{API}/variantes-producto",
        json={
            "producto_id": prod.json()["id"],
            "sku": "ELEC-FAB-01",
            "precio_venta": "80000.00",
            "control_stock": True,
        },
    )
    rec = api_client.post(
        f"{API}/recetas-producto",
        json={
            "producto_id": prod.json()["id"],
            "nombre": "Rec Elec",
            "activo": True,
            "items": [
                {
                    "material_id": mat.json()["id"],
                    "cantidad": "1",
                    "porcentaje_desperdicio": "0",
                }
            ],
        },
    )
    assert rec.status_code == 201, rec.text
    api_client.post(
        f"{API}/perfiles-costo-producto",
        json={
            "producto_id": prod.json()["id"],
            "costo_mano_obra_por_unidad": "5",
            "costo_electricidad_por_unidad": "3",
            "costo_depreciacion_por_unidad": "0",
            "costo_otros_por_unidad": "0",
            "activo": True,
        },
    )
    cli = api_client.post(f"{API}/clientes", json={"nombre": "Cli Elec"})
    pedido = api_client.post(
        f"{API}/pedidos",
        json={
            "cliente_id": cli.json()["id"],
            "items": [
                {
                    "producto_id": prod.json()["id"],
                    "variante_id": var.json()["id"],
                    "cantidad": "1",
                }
            ],
        },
    )
    assert pedido.status_code == 201, pedido.text
    conf = api_client.post(
        f"{API}/pedidos/{pedido.json()['id']}/estado",
        json={"estado_nuevo": "CONFIRMADO"},
    )
    assert conf.status_code == 200, conf.text

    op = api_client.post(
        f"{API}/ordenes-produccion",
        json={
            "pedido_id": pedido.json()["id"],
            "items": [
                {
                    "item_pedido_id": pedido.json()["items"][0]["id"],
                    "cantidad_planificada": "1",
                }
            ],
        },
    )
    assert op.status_code == 201, op.text
    item_op_id = op.json()["items"][0]["id"]

    cat_c = api_client.post(
        f"{API}/categorias-costo",
        json={"nombre": "Elec Real", "tipo_costo": "ELECTRICIDAD"},
    )
    assert cat_c.status_code == 201, cat_c.text

    ini = api_client.post(f"{API}/ordenes-produccion/{op.json()['id']}/iniciar")
    assert ini.status_code == 200, ini.text

    asiento = api_client.post(
        f"{API}/ordenes-produccion/{op.json()['id']}/items/{item_op_id}/asientos-costo",
        json={
            "categoria_costo_id": cat_c.json()["id"],
            "descripcion": "Parte factura electricidad",
            "cantidad": "1",
            "costo_unitario": "25000.00",
            "gasto_id": gid,
        },
    )
    assert asiento.status_code == 201, asiento.text

    resumen2 = api_client.get(f"{API}/finanzas/resumen")
    # Solo aseo (5000); electricidad (25000) excluida por vínculo OP
    assert Decimal(str(resumen2.json()["gastos_operativos"])) == Decimal("5000.00")
