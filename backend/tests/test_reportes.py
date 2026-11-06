"""Tests de integración Stage 9 — Reportes, dashboard y exportación."""

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
# Helpers (alineados a Stage 7)
# ---------------------------------------------------------------------------


def _metodo_y_cuenta(client: TestClient, *, sufijo: str = "") -> tuple[int, int]:
    m = client.post(f"{API}/metodos-pago", json={"nombre": f"EfectivoRep{sufijo}"})
    assert m.status_code == 201, m.text
    c = client.post(
        f"{API}/cuentas-caja",
        json={"nombre": f"CajaRep{sufijo}", "tipo_cuenta": "EFECTIVO"},
    )
    assert c.status_code == 201, c.text
    return m.json()["id"], c.json()["id"]


def _cliente_servicio_pedido(
    client: TestClient, *, precio: str = "100000.00", nombre: str = "Cli Rep"
) -> dict:
    cli = client.post(f"{API}/clientes", json={"nombre": nombre})
    assert cli.status_code == 201, cli.text
    cat = client.post(f"{API}/categorias-producto", json={"nombre": f"Cat-{nombre}"})
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
    perfil = client.post(
        f"{API}/perfiles-costo-producto",
        json={
            "producto_id": prod.json()["id"],
            "costo_mano_obra_por_unidad": "15000.00",
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
                    "cantidad": "2",
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
    for estado in ("CONFIRMADO", "LISTO", "ENTREGADO"):
        r = client.post(
            f"{API}/pedidos/{pedido_id}/estado",
            json={"estado_nuevo": estado},
        )
        assert r.status_code == 200, r.text


def _bootstrap_compra(client: TestClient) -> dict:
    cat = client.post(f"{API}/categorias-material", json={"nombre": "Mat Rep"})
    assert cat.status_code == 201, cat.text
    uni = client.post(
        f"{API}/unidades-medida",
        json={"nombre": "Unidad Rep", "abreviatura": "ur"},
    )
    assert uni.status_code == 201, uni.text
    bod = client.post(f"{API}/bodegas", json={"nombre": "Bod Rep"})
    assert bod.status_code == 201, bod.text
    mat = client.post(
        f"{API}/materiales",
        json={
            "categoria_id": cat.json()["id"],
            "unidad_id": uni.json()["id"],
            "nombre": "Vinilo Rep",
            "stock_minimo": "100",
        },
    )
    assert mat.status_code == 201, mat.text
    prov = client.post(f"{API}/proveedores", json={"nombre": "Prov Rep"})
    assert prov.status_code == 201, prov.text
    compra = client.post(
        f"{API}/compras",
        json={
            "proveedor_id": prov.json()["id"],
            "items": [
                {
                    "material_id": mat.json()["id"],
                    "cantidad": "10",
                    "costo_unitario": "50.00",
                }
            ],
        },
    )
    assert compra.status_code == 201, compra.text
    recv = client.post(
        f"{API}/compras/{compra.json()['id']}/recibir",
        json={
            "bodega_id": bod.json()["id"],
            "items": [
                {
                    "item_compra_id": compra.json()["items"][0]["id"],
                    "cantidad": "10",
                }
            ],
        },
    )
    assert recv.status_code == 200, recv.text
    return {
        "compra": recv.json(),
        "material_id": mat.json()["id"],
        "bodega_id": bod.json()["id"],
    }


def _fixture_reporte(api_client: TestClient) -> dict:
    ctx = _cliente_servicio_pedido(api_client, nombre="Rep A", precio="50000.00")
    mid, cid = _metodo_y_cuenta(api_client, sufijo="A")
    _entregar_pedido(api_client, ctx["pedido"]["id"])
    pago = api_client.post(
        f"{API}/pagos",
        json={
            "pedido_id": ctx["pedido"]["id"],
            "metodo_pago_id": mid,
            "cuenta_caja_id": cid,
            "monto": "40000.00",
            "confirmar": True,
        },
    )
    assert pago.status_code == 201, pago.text

    cat_g = api_client.post(
        f"{API}/categorias-gasto", json={"nombre": "Arriendo Rep"}
    )
    assert cat_g.status_code == 201, cat_g.text
    gasto = api_client.post(
        f"{API}/gastos",
        json={
            "categoria_id": cat_g.json()["id"],
            "descripcion": "Arriendo mes",
            "monto": "5000.00",
        },
    )
    assert gasto.status_code == 201, gasto.text

    compra = _bootstrap_compra(api_client)
    return {"pedido": ctx, "pago": pago.json(), "gasto": gasto.json(), "compra": compra}


# ---------------------------------------------------------------------------
# Endpoints de reporte
# ---------------------------------------------------------------------------


def test_ventas_diarias_y_mensuales(api_client: TestClient) -> None:
    _fixture_reporte(api_client)
    diarias = api_client.get(f"{API}/reportes/ventas/diarias")
    assert diarias.status_code == 200, diarias.text
    assert isinstance(diarias.json(), list)
    assert len(diarias.json()) >= 1
    fila = diarias.json()[0]
    assert "fecha" in fila
    assert Decimal(str(fila["total_ventas"])) > 0

    mensuales = api_client.get(f"{API}/reportes/ventas/mensuales")
    assert mensuales.status_code == 200
    assert len(mensuales.json()) >= 1
    assert "periodo" in mensuales.json()[0]


def test_productos_utilidad_rentabilidad(api_client: TestClient) -> None:
    _fixture_reporte(api_client)

    top = api_client.get(f"{API}/reportes/productos-mas-vendidos")
    assert top.status_code == 200, top.text
    assert len(top.json()) >= 1
    assert Decimal(str(top.json()[0]["cantidad_vendida"])) > 0

    util = api_client.get(f"{API}/reportes/utilidad-por-producto")
    assert util.status_code == 200
    assert len(util.json()) >= 1
    u = util.json()[0]
    assert "utilidad" in u and "margen_porcentaje" in u

    rent = api_client.get(f"{API}/reportes/rentabilidad-pedidos")
    assert rent.status_code == 200
    assert len(rent.json()) >= 1
    r = rent.json()[0]
    assert Decimal(str(r["ingreso"])) > 0
    assert "margen_porcentaje" in r


def test_compras_gastos_inventario_consumo(api_client: TestClient) -> None:
    fx = _fixture_reporte(api_client)

    compras = api_client.get(f"{API}/reportes/compras")
    assert compras.status_code == 200
    assert any(c["compra_id"] == fx["compra"]["compra"]["id"] for c in compras.json())

    gastos = api_client.get(f"{API}/reportes/gastos")
    assert gastos.status_code == 200
    assert any(g["gasto_id"] == fx["gasto"]["id"] for g in gastos.json())

    inv = api_client.get(f"{API}/reportes/inventario-valorizado")
    assert inv.status_code == 200
    assert len(inv.json()) >= 1
    assert any(i["tipo_articulo"] == "MATERIAL" for i in inv.json())
    assert Decimal(str(inv.json()[0]["valor_total"])) >= 0

    cons = api_client.get(f"{API}/reportes/consumo-materiales")
    assert cons.status_code == 200
    assert isinstance(cons.json(), list)

    desp = api_client.get(f"{API}/reportes/desperdicios")
    assert desp.status_code == 200
    assert isinstance(desp.json(), list)

    costos = api_client.get(f"{API}/reportes/costos-produccion")
    assert costos.status_code == 200
    cat = api_client.get(f"{API}/reportes/costos-por-categoria")
    assert cat.status_code == 200


def test_cuentas_pendientes_wrap(api_client: TestClient) -> None:
    _fixture_reporte(api_client)
    r = api_client.get(f"{API}/reportes/cuentas-pendientes")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "cuentas_por_cobrar" in data
    assert "cuentas_por_pagar" in data
    assert Decimal(str(data["total_cxc"])) >= 0
    # Pedido pagó 40k de ~100k → CxC > 0
    assert Decimal(str(data["total_cxc"])) > 0
    # Compra sin pago proveedor → CxP > 0
    assert Decimal(str(data["total_cxp"])) > 0


def test_dashboard_agrega_sin_error(api_client: TestClient) -> None:
    _fixture_reporte(api_client)
    r = api_client.get(f"{API}/reportes/dashboard")
    assert r.status_code == 200, r.text
    data = r.json()
    for key in (
        "ventas_dia",
        "ventas_mes",
        "dinero_recibido",
        "pedidos_pendientes",
        "pedidos_en_produccion",
        "pedidos_listos",
        "cuentas_por_cobrar",
        "gastos_mes",
        "utilidad_estimada",
        "stock_bajo",
        "costos_produccion",
        "utilidad_operativa",
        "ingresos_vs_gastos",
        "ventas_por_dia",
        "productos_mas_vendidos",
        "costos_por_categoria",
        "notas",
    ):
        assert key in data, key
    assert Decimal(str(data["dinero_recibido"])) == Decimal("40000.00")
    assert Decimal(str(data["gastos_mes"])) == Decimal("5000.00")
    assert data["stock_bajo"] >= 1  # stock_minimo=100, stock=10


# ---------------------------------------------------------------------------
# Exportación
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "tipo",
    ["ventas", "inventario-valorizado", "rentabilidad-pedidos", "resumen-financiero"],
)
@pytest.mark.parametrize("formato,ctype", [("csv", "text/csv"), ("pdf", "application/pdf")])
def test_export_content_type(
    api_client: TestClient, tipo: str, formato: str, ctype: str
) -> None:
    _fixture_reporte(api_client)
    r = api_client.get(f"{API}/reportes/export/{tipo}", params={"formato": formato})
    assert r.status_code == 200, r.text
    assert ctype in r.headers.get("content-type", "")
    assert "attachment" in r.headers.get("content-disposition", "")
    assert len(r.content) > 20
    if formato == "csv":
        text = r.content.decode("utf-8-sig")
        assert len(text.splitlines()) >= 2
    else:
        assert r.content[:4] == b"%PDF"


def test_export_tipo_invalido(api_client: TestClient) -> None:
    r = api_client.get(f"{API}/reportes/export/no-existe")
    assert r.status_code == 422
