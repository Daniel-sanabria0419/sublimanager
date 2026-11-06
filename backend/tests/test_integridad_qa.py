"""Stage 10 — integridad inventario/finanzas y carrera concurrente de pagos."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

pytestmark = pytest.mark.skipif(
    __import__("os").getenv("TEST_DATABASE_URL") is None,
    reason="Requiere TEST_DATABASE_URL",
)

API = "/api/v1"


def _money(v: object) -> Decimal:
    return Decimal(str(v))


def _metodo_y_cuenta(client: TestClient, sufijo: str) -> tuple[int, int]:
    m = client.post(f"{API}/metodos-pago", json={"nombre": f"Efec{sufijo}"})
    assert m.status_code == 201, m.text
    c = client.post(
        f"{API}/cuentas-caja",
        json={"nombre": f"Caja{sufijo}", "tipo_cuenta": "EFECTIVO"},
    )
    assert c.status_code == 201, c.text
    return m.json()["id"], c.json()["id"]


def _pedido_servicio(client: TestClient, *, precio: str, nombre: str) -> dict:
    cli = client.post(f"{API}/clientes", json={"nombre": nombre})
    assert cli.status_code == 201, cli.text
    cat = client.post(
        f"{API}/categorias-producto", json={"nombre": f"Cat-{nombre}"}
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
            "sku": f"SKU-{nombre}"[:40],
            "precio_venta": precio,
            "control_stock": False,
        },
    )
    assert var.status_code == 201, var.text
    perfil = client.post(
        f"{API}/perfiles-costo-producto",
        json={
            "producto_id": prod.json()["id"],
            "costo_mano_obra_por_unidad": "10.00",
            "activo": True,
        },
    )
    assert perfil.status_code == 201, perfil.text
    pedido = client.post(
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
    return pedido.json()


def test_integridad_movimientos_caja_un_por_pago(api_client: TestClient) -> None:
    """Cada pago CONFIRMADO genera exactamente un movimiento_caja."""
    pedido = _pedido_servicio(api_client, precio="80000.00", nombre="IntCaja")
    metodo_id, cuenta_id = _metodo_y_cuenta(api_client, "-intcaja")
    pid = pedido["id"]

    p1 = api_client.post(
        f"{API}/pagos",
        json={
            "pedido_id": pid,
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "30000.00",
            "confirmar": True,
        },
    )
    assert p1.status_code == 201, p1.text
    p2 = api_client.post(
        f"{API}/pagos",
        json={
            "pedido_id": pid,
            "metodo_pago_id": metodo_id,
            "cuenta_caja_id": cuenta_id,
            "monto": "50000.00",
            "confirmar": True,
        },
    )
    assert p2.status_code == 201, p2.text

    # Idempotencia: reconfirmar ambos
    for pago_id in (p1.json()["id"], p2.json()["id"]):
        r = api_client.post(f"{API}/pagos/{pago_id}/confirmar")
        assert r.status_code == 200, r.text

    movs = api_client.get(
        f"{API}/movimientos-caja", params={"cuenta_caja_id": cuenta_id}
    ).json()
    por_pago = {}
    for m in movs:
        pago_id = m.get("pago_id")
        if pago_id is None:
            continue
        por_pago.setdefault(pago_id, []).append(m)
    assert len(por_pago[p1.json()["id"]]) == 1
    assert len(por_pago[p2.json()["id"]]) == 1
    assert sum((_money(m["monto"]) for m in movs), Decimal("0")) == Decimal(
        "80000.00"
    )


def test_integridad_stock_vs_movimientos_compra_y_ajuste(
    api_client: TestClient,
) -> None:
    """Existencias = entradas CONFIRMADAS − salidas CONFIRMADAS."""
    cat = api_client.post(
        f"{API}/categorias-material", json={"nombre": "Cat Int Stock"}
    )
    assert cat.status_code == 201
    uni = api_client.post(
        f"{API}/unidades-medida",
        json={"nombre": "Und Int", "abreviatura": "ui"},
    )
    assert uni.status_code == 201
    bod = api_client.post(f"{API}/bodegas", json={"nombre": "Bod Int"})
    assert bod.status_code == 201
    bodega_id = bod.json()["id"]
    mat = api_client.post(
        f"{API}/materiales",
        json={
            "categoria_id": cat.json()["id"],
            "unidad_id": uni.json()["id"],
            "nombre": "Material integridad",
            "stock_minimo": "1",
        },
    )
    assert mat.status_code == 201
    mid = mat.json()["id"]

    # Entrada AJUSTE 40
    entrada = api_client.post(
        f"{API}/movimientos-inventario",
        json={
            "tipo_movimiento": "AJUSTE",
            "bodega_id": bodega_id,
            "items": [
                {
                    "material_id": mid,
                    "cantidad": "40",
                    "costo_unitario": "10.00",
                }
            ],
            "confirmar": True,
            "notas": "apertura",
        },
    )
    assert entrada.status_code == 201, entrada.text

    # Salida PRODUCCION 7 (vía movimiento directo)
    salida = api_client.post(
        f"{API}/movimientos-inventario",
        json={
            "tipo_movimiento": "PRODUCCION",
            "bodega_id": bodega_id,
            "items": [
                {
                    "material_id": mid,
                    "cantidad": "7",
                    "costo_unitario": "10.00",
                }
            ],
            "confirmar": True,
        },
    )
    assert salida.status_code == 201, salida.text

    stock = api_client.get(
        f"{API}/existencias",
        params={"bodega_id": bodega_id, "material_id": mid},
    ).json()
    assert Decimal(str(stock[0]["cantidad"])) == Decimal("33.0000")


def test_pagos_concurrentes_no_sobrepagan(api_client: TestClient, engine_test) -> None:
    """Dos hilos intentan cobrar el saldo completo; solo uno debe ganar.

    Usa PagoService + SELECT FOR UPDATE (misma garantía que la API).
    """
    from app.core.exceptions import ConflictoNegocioError
    from app.services.pagos import PagoService

    pedido = _pedido_servicio(api_client, precio="100000.00", nombre="RacePay")
    metodo_id, cuenta_id = _metodo_y_cuenta(api_client, "-race")
    pedido_id = pedido["id"]

    SessionLocal = sessionmaker(
        bind=engine_test,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )
    barrier = Barrier(2)

    def _intentar_pago() -> str:
        session = SessionLocal()
        try:
            barrier.wait(timeout=5)
            PagoService(session).registrar(
                pedido_id=pedido_id,
                metodo_pago_id=metodo_id,
                cuenta_caja_id=cuenta_id,
                monto=Decimal("100000.00"),
                confirmar=True,
                referencia="RACE",
            )
            return "ok"
        except ConflictoNegocioError:
            session.rollback()
            return "conflicto"
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            return f"error:{type(exc).__name__}:{exc}"
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(_intentar_pago) for _ in range(2)]
        resultados = [f.result(timeout=15) for f in as_completed(futures)]

    assert resultados.count("ok") == 1, resultados
    assert resultados.count("conflicto") == 1, resultados

    pagos = api_client.get(f"{API}/pagos", params={"pedido_id": pedido_id}).json()
    confirmados = [p for p in pagos if p["estado"] == "CONFIRMADO"]
    assert len(confirmados) == 1
    assert _money(confirmados[0]["monto"]) == Decimal("100000.00")

    movs = api_client.get(
        f"{API}/movimientos-caja", params={"cuenta_caja_id": cuenta_id}
    ).json()
    entradas = [m for m in movs if m.get("pago_id") == confirmados[0]["id"]]
    assert len(entradas) == 1
