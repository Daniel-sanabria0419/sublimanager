"""Routers de la API v1."""

from fastapi import APIRouter

from app.api.v1 import (
    bodegas,
    categorias_material,
    compras,
    existencias,
    health,
    materiales,
    movimientos_inventario,
    proveedores,
    unidades_medida,
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
api_router.include_router(v1)
