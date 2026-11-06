"""Routers de la API v1."""

from fastapi import APIRouter

from app.api.v1 import (
    bodegas,
    categorias_costo,
    categorias_material,
    categorias_producto,
    compras,
    existencias,
    health,
    materiales,
    movimientos_inventario,
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
api_router.include_router(v1)
