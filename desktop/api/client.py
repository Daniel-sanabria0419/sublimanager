"""Cliente HTTPX del desktop — único canal hacia FastAPI (sin SQLAlchemy/DB)."""

from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_BASE_URL = os.environ.get("SUBLIMANAGER_API_URL", "http://127.0.0.1:8000")
API_PREFIX = "/api/v1"


class ApiError(Exception):
    """Error de API o de red legible para la UI."""

    def __init__(self, message: str, *, status_code: int | None = None, detail: Any = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail


def _format_detail(detail: Any) -> str:
    if detail is None:
        return "Error desconocido"
    if isinstance(detail, str):
        return detail
    if isinstance(detail, dict):
        if "message" in detail:
            return str(detail["message"])
        if "detail" in detail:
            return _format_detail(detail["detail"])
        return str(detail)
    if isinstance(detail, list):
        parts = []
        for item in detail:
            if isinstance(item, dict):
                loc = ".".join(str(x) for x in item.get("loc", []) if x != "body")
                msg = item.get("msg", str(item))
                parts.append(f"{loc}: {msg}" if loc else msg)
            else:
                parts.append(str(item))
        return "; ".join(parts) if parts else "Error de validación"
    return str(detail)


class ApiClient:
    """Cliente REST síncrono (usar desde hilos worker, no desde el hilo UI)."""

    def __init__(self, base_url: str | None = None, timeout: float = 30.0) -> None:
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def health_db(self) -> dict[str, Any]:
        return self._request("GET", "/health/db")

    # ---- genéricos ----
    def get(self, path: str, **params: Any) -> Any:
        return self._request("GET", self._v1(path), params=params or None)

    def post(self, path: str, json: dict[str, Any] | None = None, **params: Any) -> Any:
        return self._request("POST", self._v1(path), json=json, params=params or None)

    def patch(self, path: str, json: dict[str, Any] | None = None) -> Any:
        return self._request("PATCH", self._v1(path), json=json)

    def delete(self, path: str) -> Any:
        return self._request("DELETE", self._v1(path))

    # ---- recursos de negocio (atajos) ----
    def listar_clientes(self, **params: Any) -> list[dict]:
        return self.get("/clientes", **params)

    def crear_cliente(self, data: dict) -> dict:
        return self.post("/clientes", json=data)

    def actualizar_cliente(self, cliente_id: int, data: dict) -> dict:
        return self.patch(f"/clientes/{cliente_id}", json=data)

    def eliminar_cliente(self, cliente_id: int) -> Any:
        return self.delete(f"/clientes/{cliente_id}")

    def listar_productos(self, **params: Any) -> list[dict]:
        return self.get("/productos", **params)

    def crear_producto(self, data: dict) -> dict:
        return self.post("/productos", json=data)

    def actualizar_producto(self, producto_id: int, data: dict) -> dict:
        return self.patch(f"/productos/{producto_id}", json=data)

    def costo_estimado(self, producto_id: int, **params: Any) -> dict:
        return self.get(f"/productos/{producto_id}/costo-estimado", **params)

    def listar_pedidos(self, **params: Any) -> list[dict]:
        return self.get("/pedidos", **params)

    def obtener_pedido(self, pedido_id: int) -> dict:
        return self.get(f"/pedidos/{pedido_id}")

    def crear_pedido(self, data: dict) -> dict:
        return self.post("/pedidos", json=data)

    def actualizar_pedido(self, pedido_id: int, data: dict) -> dict:
        return self.patch(f"/pedidos/{pedido_id}", json=data)

    def cambiar_estado_pedido(self, pedido_id: int, estado: str, notas: str | None = None) -> dict:
        body: dict[str, Any] = {"estado": estado}
        if notas:
            body["notas"] = notas
        return self.post(f"/pedidos/{pedido_id}/estado", json=body)

    def cancelar_pedido(self, pedido_id: int) -> dict:
        return self.post(f"/pedidos/{pedido_id}/cancelar")

    def saldo_pedido(self, pedido_id: int) -> dict:
        return self.get(f"/pedidos/{pedido_id}/saldo")

    def listar_materiales(self, **params: Any) -> list[dict]:
        return self.get("/materiales", **params)

    def crear_material(self, data: dict) -> dict:
        return self.post("/materiales", json=data)

    def actualizar_material(self, material_id: int, data: dict) -> dict:
        return self.patch(f"/materiales/{material_id}", json=data)

    def alertas_stock_bajo(self) -> list[dict]:
        return self.get("/materiales/alertas-stock-bajo")

    def listar_existencias(self, **params: Any) -> list[dict]:
        return self.get("/existencias", **params)

    def listar_movimientos(self, **params: Any) -> list[dict]:
        return self.get("/movimientos-inventario", **params)

    def crear_movimiento(self, data: dict) -> dict:
        return self.post("/movimientos-inventario", json=data)

    def confirmar_movimiento(self, movimiento_id: int) -> dict:
        return self.post(f"/movimientos-inventario/{movimiento_id}/confirmar")

    def crear_transferencia(self, data: dict) -> dict:
        return self.post("/movimientos-inventario/transferencias", json=data)

    def listar_proveedores(self, **params: Any) -> list[dict]:
        return self.get("/proveedores", **params)

    def crear_proveedor(self, data: dict) -> dict:
        return self.post("/proveedores", json=data)

    def actualizar_proveedor(self, proveedor_id: int, data: dict) -> dict:
        return self.patch(f"/proveedores/{proveedor_id}", json=data)

    def eliminar_proveedor(self, proveedor_id: int) -> Any:
        return self.delete(f"/proveedores/{proveedor_id}")

    def listar_compras(self, **params: Any) -> list[dict]:
        return self.get("/compras", **params)

    def crear_compra(self, data: dict) -> dict:
        return self.post("/compras", json=data)

    def recibir_compra(self, compra_id: int, data: dict | None = None) -> dict:
        return self.post(f"/compras/{compra_id}/recibir", json=data)

    def cancelar_compra(self, compra_id: int) -> dict:
        return self.post(f"/compras/{compra_id}/cancelar")

    def listar_ordenes_produccion(self, **params: Any) -> list[dict]:
        return self.get("/ordenes-produccion", **params)

    def crear_orden_produccion(self, data: dict) -> dict:
        return self.post("/ordenes-produccion", json=data)

    def iniciar_orden(self, orden_id: int) -> dict:
        return self.post(f"/ordenes-produccion/{orden_id}/iniciar")

    def cancelar_orden(self, orden_id: int) -> dict:
        return self.post(f"/ordenes-produccion/{orden_id}/cancelar")

    def completar_orden(self, orden_id: int, data: dict | None = None) -> dict:
        return self.post(f"/ordenes-produccion/{orden_id}/completar", json=data)

    def materiales_requeridos(self, orden_id: int, **params: Any) -> dict:
        return self.get(f"/ordenes-produccion/{orden_id}/materiales-requeridos", **params)

    def listar_recetas(self, **params: Any) -> list[dict]:
        return self.get("/recetas-producto", **params)

    def crear_receta(self, data: dict) -> dict:
        return self.post("/recetas-producto", json=data)

    def activar_receta(self, receta_id: int) -> dict:
        return self.post(f"/recetas-producto/{receta_id}/activar")

    def listar_pagos(self, **params: Any) -> list[dict]:
        return self.get("/pagos", **params)

    def crear_pago(self, data: dict) -> dict:
        return self.post("/pagos", json=data)

    def confirmar_pago(self, pago_id: int) -> dict:
        return self.post(f"/pagos/{pago_id}/confirmar")

    def anular_pago(self, pago_id: int) -> dict:
        return self.post(f"/pagos/{pago_id}/anular")

    def listar_gastos(self, **params: Any) -> list[dict]:
        return self.get("/gastos", **params)

    def crear_gasto(self, data: dict) -> dict:
        return self.post("/gastos", json=data)

    def anular_gasto(self, gasto_id: int) -> dict:
        return self.post(f"/gastos/{gasto_id}/anular")

    def listar_pagos_gasto(self, **params: Any) -> list[dict]:
        return self.get("/pagos-gasto", **params)

    def crear_pago_gasto(self, data: dict) -> dict:
        return self.post("/pagos-gasto", json=data)

    def listar_pagos_proveedor(self, **params: Any) -> list[dict]:
        return self.get("/pagos-proveedor", **params)

    def crear_pago_proveedor(self, data: dict) -> dict:
        return self.post("/pagos-proveedor", json=data)

    def listar_movimientos_caja(self, **params: Any) -> list[dict]:
        return self.get("/movimientos-caja", **params)

    def cuentas_por_cobrar(self) -> list[dict]:
        return self.get("/finanzas/cuentas-por-cobrar")

    def cuentas_por_pagar(self) -> list[dict]:
        return self.get("/finanzas/cuentas-por-pagar")

    def resumen_financiero(self, **params: Any) -> dict:
        return self.get("/finanzas/resumen", **params)

    # ---- Reportes Stage 9 ----
    def dashboard_reportes(self, **params: Any) -> dict:
        return self.get("/reportes/dashboard", **params)

    def reporte_ventas_diarias(self, **params: Any) -> list[dict]:
        return self.get("/reportes/ventas/diarias", **params)

    def reporte_ventas_mensuales(self, **params: Any) -> list[dict]:
        return self.get("/reportes/ventas/mensuales", **params)

    def reporte_productos_mas_vendidos(self, **params: Any) -> list[dict]:
        return self.get("/reportes/productos-mas-vendidos", **params)

    def reporte_utilidad_por_producto(self, **params: Any) -> list[dict]:
        return self.get("/reportes/utilidad-por-producto", **params)

    def reporte_rentabilidad_pedidos(self, **params: Any) -> list[dict]:
        return self.get("/reportes/rentabilidad-pedidos", **params)

    def reporte_costos_produccion(self, **params: Any) -> list[dict]:
        return self.get("/reportes/costos-produccion", **params)

    def reporte_costos_por_categoria(self, **params: Any) -> list[dict]:
        return self.get("/reportes/costos-por-categoria", **params)

    def reporte_compras(self, **params: Any) -> list[dict]:
        return self.get("/reportes/compras", **params)

    def reporte_gastos(self, **params: Any) -> list[dict]:
        return self.get("/reportes/gastos", **params)

    def reporte_inventario_valorizado(self, **params: Any) -> list[dict]:
        return self.get("/reportes/inventario-valorizado", **params)

    def reporte_consumo_materiales(self, **params: Any) -> list[dict]:
        return self.get("/reportes/consumo-materiales", **params)

    def reporte_desperdicios(self, **params: Any) -> list[dict]:
        return self.get("/reportes/desperdicios", **params)

    def reporte_cuentas_pendientes(self, **params: Any) -> dict:
        return self.get("/reportes/cuentas-pendientes", **params)

    def exportar_reporte(self, tipo: str, *, formato: str = "csv") -> tuple[bytes, str]:
        """Descarga CSV/PDF; retorna (contenido, nombre_sugerido)."""
        path = self._v1(f"/reportes/export/{tipo}")
        try:
            response = self._client.get(path, params={"formato": formato})
        except httpx.ConnectError as exc:
            raise ApiError(
                "No se pudo conectar con la API. ¿Está corriendo el backend en "
                f"{self.base_url}?"
            ) from exc
        except httpx.TimeoutException as exc:
            raise ApiError("La API no respondió a tiempo.") from exc
        except httpx.HTTPError as exc:
            raise ApiError(f"Error de red: {exc}") from exc

        if not response.is_success:
            detail: Any
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            payload = None
            if isinstance(detail, dict):
                payload = detail.get("detalle", detail.get("detail", detail))
            else:
                payload = detail
            raise ApiError(
                _format_detail(payload),
                status_code=response.status_code,
                detail=detail,
            )

        filename = f"reporte-{tipo}.{formato}"
        cd = response.headers.get("content-disposition") or ""
        if "filename=" in cd:
            filename = cd.split("filename=")[-1].strip().strip('"')
        return response.content, filename

    def listar_metodos_pago(self, **params: Any) -> list[dict]:
        return self.get("/metodos-pago", **params)

    def crear_metodo_pago(self, data: dict) -> dict:
        return self.post("/metodos-pago", json=data)

    def actualizar_metodo_pago(self, metodo_id: int, data: dict) -> dict:
        return self.patch(f"/metodos-pago/{metodo_id}", json=data)

    def eliminar_metodo_pago(self, metodo_id: int) -> Any:
        return self.delete(f"/metodos-pago/{metodo_id}")

    def listar_cuentas_caja(self, **params: Any) -> list[dict]:
        return self.get("/cuentas-caja", **params)

    def crear_cuenta_caja(self, data: dict) -> dict:
        return self.post("/cuentas-caja", json=data)

    def actualizar_cuenta_caja(self, cuenta_id: int, data: dict) -> dict:
        return self.patch(f"/cuentas-caja/{cuenta_id}", json=data)

    def eliminar_cuenta_caja(self, cuenta_id: int) -> Any:
        return self.delete(f"/cuentas-caja/{cuenta_id}")

    def saldos_caja(self) -> list[dict]:
        return self.get("/cuentas-caja/saldos")

    def listar_bodegas(self, **params: Any) -> list[dict]:
        return self.get("/bodegas", **params)

    def crear_bodega(self, data: dict) -> dict:
        return self.post("/bodegas", json=data)

    def listar_unidades(self, **params: Any) -> list[dict]:
        return self.get("/unidades-medida", **params)

    def crear_unidad(self, data: dict) -> dict:
        return self.post("/unidades-medida", json=data)

    def actualizar_unidad(self, unidad_id: int, data: dict) -> dict:
        return self.patch(f"/unidades-medida/{unidad_id}", json=data)

    def eliminar_unidad(self, unidad_id: int) -> Any:
        return self.delete(f"/unidades-medida/{unidad_id}")

    def listar_categorias_material(self, **params: Any) -> list[dict]:
        return self.get("/categorias-material", **params)

    def crear_categoria_material(self, data: dict) -> dict:
        return self.post("/categorias-material", json=data)

    def listar_categorias_producto(self, **params: Any) -> list[dict]:
        return self.get("/categorias-producto", **params)

    def crear_categoria_producto(self, data: dict) -> dict:
        return self.post("/categorias-producto", json=data)

    def listar_categorias_gasto(self, **params: Any) -> list[dict]:
        return self.get("/categorias-gasto", **params)

    def crear_categoria_gasto(self, data: dict) -> dict:
        return self.post("/categorias-gasto", json=data)

    def listar_categorias_costo(self, **params: Any) -> list[dict]:
        return self.get("/categorias-costo", **params)

    def listar_variantes(self, **params: Any) -> list[dict]:
        return self.get("/variantes-producto", **params)

    def crear_variante(self, data: dict) -> dict:
        return self.post("/variantes-producto", json=data)

    def _v1(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{API_PREFIX}{path}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        try:
            response = self._client.request(method, path, json=json, params=params)
        except httpx.ConnectError as exc:
            raise ApiError(
                "No se pudo conectar con la API. ¿Está corriendo el backend en "
                f"{self.base_url}?"
            ) from exc
        except httpx.TimeoutException as exc:
            raise ApiError("La API no respondió a tiempo.") from exc
        except httpx.HTTPError as exc:
            raise ApiError(f"Error de red: {exc}") from exc

        if response.status_code == 204:
            return None

        data: Any
        try:
            data = response.json() if response.content else None
        except ValueError:
            data = response.text

        if response.is_success:
            return data

        detail = data.get("detail") if isinstance(data, dict) else data
        raise ApiError(
            _format_detail(detail),
            status_code=response.status_code,
            detail=detail,
        )
