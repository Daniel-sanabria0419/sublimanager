"""Routers de la API v1."""

from fastapi import APIRouter

from app.api.v1 import (
    bodegas,
    categorias_costo,
    categorias_gasto,
    categorias_material,
    categorias_producto,
    clientes,
    compras,
    cuentas_caja,
    existencias,
    finanzas,
    gastos,
    health,
    materiales,
    metodos_pago,
    movimientos_caja,
    movimientos_inventario,
    ordenes_produccion,
    pagos,
    pagos_gasto,
    pagos_proveedor,
    pedidos,
    perfiles_costo_producto,
    productos,
    proveedores,
    recetas_producto,
    tecnicas_produccion,
    tecnicas_producto,
    unidades_medida,
    variantes_producto,
)
from app.core.constants import API_V1_PREFIX

api_router = APIRouter()

# Salud en la raíz (Stage 1)
api_router.include_router(health.router)

# Recursos de negocio bajo /api/v1 (Stage 3+)
v1 = APIRouter(prefix=API_V1_PREFIX)
v1.include_router(categorias_material.router)
v1.include_router(unidades_medida.router)
v1.include_router(bodegas.router)
v1.include_router(materiales.router)
v1.include_router(existencias.router)
v1.include_router(movimientos_inventario.router)
v1.include_router(proveedores.router)
v1.include_router(compras.router)
# Stage 4 — productos y recetas
v1.include_router(categorias_producto.router)
v1.include_router(productos.router)
v1.include_router(variantes_producto.router)
v1.include_router(tecnicas_produccion.router)
v1.include_router(tecnicas_producto.router)
v1.include_router(categorias_costo.router)
v1.include_router(recetas_producto.router)
v1.include_router(perfiles_costo_producto.router)
# Stage 5 — clientes, pedidos, anticipos mínimos
v1.include_router(clientes.router)
v1.include_router(pedidos.router)
v1.include_router(metodos_pago.router)
v1.include_router(cuentas_caja.router)
v1.include_router(pagos.router)
# Stage 6 — órdenes de producción
v1.include_router(ordenes_produccion.router)
# Stage 7 — finanzas (extiende pagos/caja Stage 5)
v1.include_router(categorias_gasto.router)
v1.include_router(gastos.router)
v1.include_router(pagos_gasto.router)
v1.include_router(pagos_proveedor.router)
v1.include_router(movimientos_caja.router)
v1.include_router(finanzas.router)
api_router.include_router(v1)
