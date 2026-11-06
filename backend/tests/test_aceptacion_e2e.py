"""Stage 10 — escenario integral de aceptación (vaso sublimable).

Flujo API en español: proveedor → compra → producto/receta → pedido →
anticipo → OP → consumos/desperdicios → costo real → LISTO → pago → ENTREGADO.
Verifica finanzas, caja e inventario sin dobles descuentos ni movimientos
duplicados.
"""

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


def _money(v: object) -> Decimal:
    return Decimal(str(v))


def _qty(v: object) -> Decimal:
    return Decimal(str(v))


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
    return _qty(filas[0]["cantidad"])


def _stock_variante(
    client: TestClient, *, bodega_id: int, variante_id: int
) -> Decimal:
    resp = client.get(f"{API}/existencias", params={"bodega_id": bodega_id})
    assert resp.status_code == 200, resp.text
    for fila in resp.json():
        if fila.get("variante_producto_id") == variante_id:
            return _qty(fila["cantidad"])
    return Decimal("0")


def _unidad(client: TestClient, nombre: str, abrev: str) -> int:
    r = client.post(
        f"{API}/unidades-medida",
        json={"nombre": nombre, "abreviatura": abrev},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _material(
    client: TestClient,
    *,
    categoria_id: int,
    unidad_id: int,
    nombre: str,
) -> dict:
    r = client.post(
        f"{API}/materiales",
        json={
            "categoria_id": categoria_id,
            "unidad_id": unidad_id,
            "nombre": nombre,
            "stock_minimo": "5",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def _categoria_costo(client: TestClient, nombre: str, tipo: str) -> int:
    r = client.post(
        f"{API}/categorias-costo",
        json={"nombre": nombre, "tipo_costo": tipo},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


# ---------------------------------------------------------------------------
# Escenario §10
# ---------------------------------------------------------------------------


def test_escenario_aceptacion_vaso_sublimable(api_client: TestClient) -> None:
    """Walkthrough completo del vaso personalizado (pasos 1–26 del §10)."""
    c = api_client

    # --- 1–3. Catálogo base: categorías, unidades, bodega, proveedor --------
    cat_mat = c.post(
        f"{API}/categorias-material",
        json={"nombre": "Insumos sublimación", "descripcion": "Base V1"},
    )
    assert cat_mat.status_code == 201, cat_mat.text
    cat_mat_id = cat_mat.json()["id"]

    u_und = _unidad(c, "Unidad", "und")
    u_hoja = _unidad(c, "Hoja", "hoja")
    u_ml = _unidad(c, "Mililitro", "ml")
    u_m = _unidad(c, "Metro", "m")

    bod = c.post(
        f"{API}/bodegas",
        json={"nombre": "Taller principal", "ubicacion": "Planta"},
    )
    assert bod.status_code == 201, bod.text
    bodega_id = bod.json()["id"]

    prov = c.post(
        f"{API}/proveedores",
        json={
            "nombre": "Proveedor Sublimación SAS",
            "identificacion": "900111222",
        },
    )
    assert prov.status_code == 201, prov.text
    proveedor_id = prov.json()["id"]

    # --- 4–6. Materiales (sin stock inicial; entrada vía compra) -----------
    vaso = _material(
        c, categoria_id=cat_mat_id, unidad_id=u_und, nombre="Vaso Sublimable"
    )
    papel = _material(
        c, categoria_id=cat_mat_id, unidad_id=u_hoja, nombre="Hoja papel sublimación"
    )
    tinta = _material(
        c, categoria_id=cat_mat_id, unidad_id=u_ml, nombre="Tinta sublimación"
    )
    cinta = _material(
        c, categoria_id=cat_mat_id, unidad_id=u_m, nombre="Cinta térmica"
    )

    assert _stock_material(c, bodega_id=bodega_id, material_id=vaso["id"]) == Decimal(
        "0"
    )

    # --- 7–8. Compra 100 vasos + insumos auxiliares → recepción ------------
    # Costos unitarios de compra (COP-like):
    # vaso 2000 | papel 500 | tinta 40/ml | cinta 1000/m
    compra = c.post(
        f"{API}/compras",
        json={
            "proveedor_id": proveedor_id,
            "numero_factura": "FAC-VASO-001",
            "items": [
                {
                    "material_id": vaso["id"],
                    "cantidad": "100",
                    "costo_unitario": "2000.00",
                },
                {
                    "material_id": papel["id"],
                    "cantidad": "50",
                    "costo_unitario": "500.00",
                },
                {
                    "material_id": tinta["id"],
                    "cantidad": "200",
                    "costo_unitario": "40.00",
                },
                {
                    "material_id": cinta["id"],
                    "cantidad": "20",
                    "costo_unitario": "1000.00",
                },
            ],
        },
    )
    assert compra.status_code == 201, compra.text
    compra_body = compra.json()
    assert compra_body["estado"] == "BORRADOR"

    recv = c.post(
        f"{API}/compras/{compra_body['id']}/recibir",
        json={
            "bodega_id": bodega_id,
            "items": [
                {"item_compra_id": it["id"], "cantidad": it["cantidad"]}
                for it in compra_body["items"]
            ],
        },
    )
    assert recv.status_code == 200, recv.text
    assert recv.json()["estado"] == "RECIBIDA"

    assert _stock_material(c, bodega_id=bodega_id, material_id=vaso["id"]) == Decimal(
        "100.0000"
    )
    assert _stock_material(c, bodega_id=bodega_id, material_id=papel["id"]) == Decimal(
        "50.0000"
    )
    assert _stock_material(c, bodega_id=bodega_id, material_id=tinta["id"]) == Decimal(
        "200.0000"
    )
    assert _stock_material(c, bodega_id=bodega_id, material_id=cinta["id"]) == Decimal(
        "20.0000"
    )

    vaso_detalle = c.get(f"{API}/materiales/{vaso['id']}").json()
    assert _money(vaso_detalle["costo_promedio"]) == Decimal("2000.00")

    # --- 9–12. Producto FABRICADO + receta + perfil de costo --------------
    cat_prod = c.post(
        f"{API}/categorias-producto",
        json={"nombre": "Vasos personalizados"},
    )
    assert cat_prod.status_code == 201, cat_prod.text

    prod = c.post(
        f"{API}/productos",
        json={
            "categoria_id": cat_prod.json()["id"],
            "nombre": "Vaso Personalizado",
            "tipo_producto": "FABRICADO",
            "descripcion": "Vaso sublimable personalizado",
        },
    )
    assert prod.status_code == 201, prod.text
    producto_id = prod.json()["id"]

    var = c.post(
        f"{API}/variantes-producto",
        json={
            "producto_id": producto_id,
            "sku": "VASO-PERS-11oz",
            "talla": "11oz",
            "color": "Blanco",
            "precio_venta": "15000.00",
            "control_stock": True,
        },
    )
    assert var.status_code == 201, var.text
    variante_id = var.json()["id"]

    # Receta por vaso: 1 vaso, 1 hoja, 5 ml tinta, 0,2 m cinta
    # Desperdicio estimado: papel 5%, tinta 10%
    receta = c.post(
        f"{API}/recetas-producto",
        json={
            "producto_id": producto_id,
            "variante_id": variante_id,
            "nombre": "BOM Vaso Personalizado",
            "activo": True,
            "items": [
                {
                    "material_id": vaso["id"],
                    "cantidad": "1",
                    "porcentaje_desperdicio": "0",
                },
                {
                    "material_id": papel["id"],
                    "cantidad": "1",
                    "porcentaje_desperdicio": "5",
                },
                {
                    "material_id": tinta["id"],
                    "cantidad": "5",
                    "porcentaje_desperdicio": "10",
                },
                {
                    "material_id": cinta["id"],
                    "cantidad": "0.2",
                    "porcentaje_desperdicio": "0",
                },
            ],
        },
    )
    assert receta.status_code == 201, receta.text

    perfil = c.post(
        f"{API}/perfiles-costo-producto",
        json={
            "producto_id": producto_id,
            "variante_id": variante_id,
            "costo_mano_obra_por_unidad": "1500.00",
            "costo_electricidad_por_unidad": "300.00",
            "costo_depreciacion_por_unidad": "200.00",
            "costo_otros_por_unidad": "0",
            "activo": True,
        },
    )
    assert perfil.status_code == 201, perfil.text

    # --- 13. Costo estimado unitario --------------------------------------
    # mat = 2000 + 500*1.05 + 40*5*1.10 + 1000*0.2 = 2945
    # + 1500 + 300 + 200 = 4945
    est = c.get(
        f"{API}/productos/{producto_id}/costo-estimado",
        params={"variante_id": variante_id},
    )
    assert est.status_code == 200, est.text
    est_body = est.json()
    assert _money(est_body["costo_materiales"]) == Decimal("2945.00")
    assert _money(est_body["costo_mano_obra"]) == Decimal("1500.00")
    assert _money(est_body["costo_electricidad"]) == Decimal("300.00")
    assert _money(est_body["costo_depreciacion"]) == Decimal("200.00")
    assert _money(est_body["costo_estimado"]) == Decimal("4945.00")
    assert _money(est_body["precio_venta"]) == Decimal("15000.00")
    assert _money(est_body["utilidad"]) == Decimal("10055.00")

    # --- 14–16. Cliente + pedido 10 vasos + confirmación ------------------
    cli = c.post(
        f"{API}/clientes",
        json={
            "nombre": "Ana Cliente",
            "identificacion": "10203040",
            "telefono": "3001234567",
        },
    )
    assert cli.status_code == 201, cli.text

    pedido = c.post(
        f"{API}/pedidos",
        json={
            "cliente_id": cli.json()["id"],
            "descuento": "0",
            "items": [
                {
                    "producto_id": producto_id,
                    "variante_id": variante_id,
                    "cantidad": "10",
                }
            ],
        },
    )
    assert pedido.status_code == 201, pedido.text
    pedido_body = pedido.json()
    assert pedido_body["estado"] == "PENDIENTE"
    assert _money(pedido_body["total"]) == Decimal("150000.00")
    item_pedido_id = pedido_body["items"][0]["id"]
    assert _money(pedido_body["items"][0]["costo_unitario_estimado"]) == Decimal(
        "4945.00"
    )

    conf = c.post(
        f"{API}/pedidos/{pedido_body['id']}/estado",
        json={"estado_nuevo": "CONFIRMADO"},
    )
    assert conf.status_code == 200, conf.text

    # Pedido NO descuenta materiales
    assert _stock_material(c, bodega_id=bodega_id, material_id=vaso["id"]) == Decimal(
        "100.0000"
    )

    # --- 17. Anticipo -----------------------------------------------------
    metodo = c.post(f"{API}/metodos-pago", json={"nombre": "Efectivo taller"})
    assert metodo.status_code == 201, metodo.text
    cuenta = c.post(
        f"{API}/cuentas-caja",
        json={"nombre": "Caja principal", "tipo_cuenta": "EFECTIVO"},
    )
    assert cuenta.status_code == 201, cuenta.text
    metodo_id, cuenta_id = metodo.json()["id"], cuenta.json()["id"]

    anticipo = c.post(
        f"{API}/pagos",
        json={
            "pedido_id": pedido_body["id"],
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "50000.00",
            "referencia": "ANTICIPO-1",
            "confirmar": True,
        },
    )
    assert anticipo.status_code == 201, anticipo.text
    anticipo_id = anticipo.json()["id"]
    assert anticipo.json()["estado"] == "CONFIRMADO"

    # Reconfirmación idempotente: un solo movimiento de caja
    reconf = c.post(f"{API}/pagos/{anticipo_id}/confirmar")
    assert reconf.status_code == 200, reconf.text
    movs_caja_anticipo = c.get(
        f"{API}/movimientos-caja",
        params={"cuenta_caja_id": cuenta_id},
    )
    assert movs_caja_anticipo.status_code == 200
    movs_pago = [
        m for m in movs_caja_anticipo.json() if m.get("pago_id") == anticipo_id
    ]
    assert len(movs_pago) == 1

    # --- 18–19. OP + disponibilidad ---------------------------------------
    en_prod = c.post(
        f"{API}/pedidos/{pedido_body['id']}/estado",
        json={"estado_nuevo": "EN_PRODUCCION"},
    )
    assert en_prod.status_code == 200, en_prod.text

    op = c.post(
        f"{API}/ordenes-produccion",
        json={
            "pedido_id": pedido_body["id"],
            "items": [
                {
                    "item_pedido_id": item_pedido_id,
                    "cantidad_planificada": "10",
                }
            ],
            "notas": "OP vaso sublimable aceptación",
        },
    )
    assert op.status_code == 201, op.text
    op_body = op.json()
    assert op_body["estado"] == "PLANIFICADA"
    item_op_id = op_body["items"][0]["id"]

    req = c.get(
        f"{API}/ordenes-produccion/{op_body['id']}/materiales-requeridos",
        params={"bodega_id": bodega_id},
    )
    assert req.status_code == 200, req.text
    req_body = req.json()
    assert req_body["todos_suficientes"] is True
    por_mat = {m["material_id"]: m for m in req_body["materiales"]}
    assert _qty(por_mat[vaso["id"]]["cantidad_requerida"]) == Decimal("10.0000")
    assert _qty(por_mat[papel["id"]]["cantidad_requerida"]) == Decimal("10.5000")
    assert _qty(por_mat[tinta["id"]]["cantidad_requerida"]) == Decimal("55.0000")
    assert _qty(por_mat[cinta["id"]]["cantidad_requerida"]) == Decimal("2.0000")

    ini = c.post(f"{API}/ordenes-produccion/{op_body['id']}/iniciar")
    assert ini.status_code == 200, ini.text
    assert ini.json()["estado"] == "EN_PROCESO"

    # --- 20. Consumos productivos + desperdicios reales -------------------
    consumos_prod = [
        (vaso["id"], "10", False),
        (papel["id"], "10", False),
        (tinta["id"], "50", False),
        (cinta["id"], "2", False),
    ]
    consumos_desp = [
        (papel["id"], "1", True),
        (tinta["id"], "5", True),
    ]
    for mat_id, qty, es_desp in consumos_prod + consumos_desp:
        r = c.post(
            f"{API}/ordenes-produccion/{op_body['id']}/items/{item_op_id}/consumos",
            params={"bodega_id": bodega_id},
            json={
                "material_id": mat_id,
                "cantidad_consumida": qty,
                "es_desperdicio": es_desp,
            },
        )
        assert r.status_code == 201, r.text

    # Stock tras consumos (una sola vez): 100-10, 50-11, 200-55, 20-2
    assert _stock_material(c, bodega_id=bodega_id, material_id=vaso["id"]) == Decimal(
        "90.0000"
    )
    assert _stock_material(c, bodega_id=bodega_id, material_id=papel["id"]) == Decimal(
        "39.0000"
    )
    assert _stock_material(c, bodega_id=bodega_id, material_id=tinta["id"]) == Decimal(
        "145.0000"
    )
    assert _stock_material(c, bodega_id=bodega_id, material_id=cinta["id"]) == Decimal(
        "18.0000"
    )

    # Un movimiento CONFIRMADO por consumo (PRODUCCION o DESPERDICIO)
    movs_prod = c.get(
        f"{API}/movimientos-inventario",
        params={"tipo_movimiento": "PRODUCCION", "bodega_id": bodega_id},
    ).json()
    movs_desp = c.get(
        f"{API}/movimientos-inventario",
        params={"tipo_movimiento": "DESPERDICIO", "bodega_id": bodega_id},
    ).json()
    conf_prod = [m for m in movs_prod if m["estado"] == "CONFIRMADO"]
    conf_desp = [m for m in movs_desp if m["estado"] == "CONFIRMADO"]
    assert len(conf_prod) == 4
    assert len(conf_desp) == 2

    # --- 21. Asientos REAL no materiales + cantidades + cierre ------------
    cat_mo = _categoria_costo(c, "Mano de obra vaso", "MANO_OBRA")
    cat_el = _categoria_costo(c, "Electricidad vaso", "ELECTRICIDAD")
    cat_dep = _categoria_costo(c, "Depreciación vaso", "DEPRECIACION")

    for cat_id, unitario in (
        (cat_mo, "1500.00"),
        (cat_el, "300.00"),
        (cat_dep, "200.00"),
    ):
        asiento = c.post(
            f"{API}/ordenes-produccion/{op_body['id']}/items/{item_op_id}/asientos-costo",
            json={
                "categoria_costo_id": cat_id,
                "cantidad": "10",
                "costo_unitario": unitario,
            },
        )
        assert asiento.status_code == 201, asiento.text

    cant = c.post(
        f"{API}/ordenes-produccion/{op_body['id']}/items/{item_op_id}/cantidades",
        json={
            "cantidad_producida": "10",
            "cantidad_rechazada": "0",
            "bodega_producto_id": bodega_id,
        },
    )
    assert cant.status_code == 200, cant.text
    assert _stock_variante(c, bodega_id=bodega_id, variante_id=variante_id) == Decimal(
        "10.0000"
    )

    cierre = c.post(
        f"{API}/ordenes-produccion/{op_body['id']}/completar",
        json={"bodega_producto_id": bodega_id},
    )
    assert cierre.status_code == 200, cierre.text
    assert cierre.json()["estado"] == "COMPLETADA"

    # Costo real: materiales 29700 + MO 15000 + elec 3000 + dep 2000 = 49700
    # Por vaso: 4970.00
    cmp_ = c.get(
        f"{API}/ordenes-produccion/{op_body['id']}/comparacion-costos"
    )
    assert cmp_.status_code == 200, cmp_.text
    cmp_body = cmp_.json()
    assert _money(cmp_body["items"][0]["costo_materiales_consumos"]) == Decimal(
        "29700.00"
    )
    assert _money(cmp_body["costo_real_total"]) == Decimal("49700.00")
    assert _money(cmp_body["costo_estimado_total"]) == Decimal("49450.00")  # 10*4945
    costo_real_por_vaso = _money(cmp_body["costo_real_total"]) / Decimal("10")
    assert costo_real_por_vaso == Decimal("4970.00")

    real_por_tipo = cmp_body["items"][0]["real_por_tipo"]
    assert _money(real_por_tipo.get("MATERIAL", "0")) == Decimal("29700.00")
    assert _money(real_por_tipo.get("MANO_OBRA", "0")) == Decimal("15000.00")
    assert _money(real_por_tipo.get("ELECTRICIDAD", "0")) == Decimal("3000.00")
    assert _money(real_por_tipo.get("DEPRECIACION", "0")) == Decimal("2000.00")

    # Desperdicio real valorizado: 1*500 + 5*40 = 700
    costo_desperdicio = Decimal("700.00")
    assert costo_desperdicio == Decimal("700.00")

    # --- 22–24. LISTO → pago restante → ENTREGADO -------------------------
    listo = c.post(
        f"{API}/pedidos/{pedido_body['id']}/estado",
        json={"estado_nuevo": "LISTO"},
    )
    assert listo.status_code == 200, listo.text

    resto = c.post(
        f"{API}/pagos",
        json={
            "pedido_id": pedido_body["id"],
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "100000.00",
            "referencia": "SALDO-FINAL",
            "confirmar": True,
        },
    )
    assert resto.status_code == 201, resto.text
    resto_id = resto.json()["id"]

    # No se puede sobrepagar
    over = c.post(
        f"{API}/pagos",
        json={
            "pedido_id": pedido_body["id"],
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "1.00",
            "confirmar": True,
        },
    )
    assert over.status_code == 409, over.text

    entregado = c.post(
        f"{API}/pedidos/{pedido_body['id']}/estado",
        json={"estado_nuevo": "ENTREGADO"},
    )
    assert entregado.status_code == 200, entregado.text
    assert entregado.json()["estado"] == "ENTREGADO"

    # --- 25–26. Finanzas / caja / integridad ------------------------------
    resumen = c.get(f"{API}/finanzas/resumen")
    assert resumen.status_code == 200, resumen.text
    fin = resumen.json()
    assert _money(fin["ventas_reconocidas"]) == Decimal("150000.00")
    assert _money(fin["dinero_recibido"]) == Decimal("150000.00")
    assert _money(fin["cuentas_por_cobrar"]) == Decimal("0.00")
    assert _money(fin["costos_produccion"]) == Decimal("49700.00")
    assert _money(fin["utilidad_bruta"]) == Decimal("100300.00")
    assert _money(fin["entradas_caja"]) == Decimal("150000.00")
    assert _money(fin["saldo_caja_neto"]) == Decimal("150000.00")

    todos_movs_caja = c.get(
        f"{API}/movimientos-caja",
        params={"cuenta_caja_id": cuenta_id},
    ).json()
    entradas = [
        m
        for m in todos_movs_caja
        if m["tipo_movimiento"] == "ENTRADA"
        and m.get("pago_id") in {anticipo_id, resto_id}
    ]
    assert len(entradas) == 2
    assert sum((_money(m["monto"]) for m in entradas), Decimal("0")) == Decimal(
        "150000.00"
    )

    # Stock final materiales intacto (sin segundo descuento al entregar)
    assert _stock_material(c, bodega_id=bodega_id, material_id=vaso["id"]) == Decimal(
        "90.0000"
    )
    assert _stock_material(c, bodega_id=bodega_id, material_id=papel["id"]) == Decimal(
        "39.0000"
    )
    assert _stock_material(c, bodega_id=bodega_id, material_id=tinta["id"]) == Decimal(
        "145.0000"
    )
    assert _stock_material(c, bodega_id=bodega_id, material_id=cinta["id"]) == Decimal(
        "18.0000"
    )

    # PT permanece en bodega (FABRICADO no sale en ENTREGADO — §5.3 solo REVENTA)
    assert _stock_variante(c, bodega_id=bodega_id, variante_id=variante_id) == Decimal(
        "10.0000"
    )

    # CxC vacía para este pedido
    cxc = c.get(f"{API}/finanzas/cuentas-por-cobrar").json()
    assert all(row["pedido_id"] != pedido_body["id"] for row in cxc)

    # Respuestas clave del escenario (assert + documentación viva)
    assert {
        "costo_fabricacion_por_vaso": str(costo_real_por_vaso),
        "materiales": "29700.00",
        "mano_obra": "15000.00",
        "electricidad": "3000.00",
        "depreciacion": "2000.00",
        "desperdicio": "700.00",
        "cobrado_total": "150000.00",
        "recibido": "150000.00",
        "pendiente": "0.00",
        "utilidad_pedido": "100300.00",
        "stock_vaso": "90.0000",
        "stock_papel": "39.0000",
        "stock_tinta": "145.0000",
        "stock_cinta": "18.0000",
        "stock_pt": "10.0000",
    }
