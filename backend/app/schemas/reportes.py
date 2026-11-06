"""Schemas Pydantic de reportes y dashboard (Stage 9)."""

from __future__ import annotations

from decimal import Decimal

from pydantic import Field

from app.schemas.common import OrmModel
from app.schemas.finanzas import CuentaPorCobrarOut, CuentaPorPagarOut


class VentaDiariaOut(OrmModel):
    fecha: str | None
    cantidad_pedidos: int
    total_ventas: Decimal


class VentaMensualOut(OrmModel):
    anio: int
    mes: int
    periodo: str
    cantidad_pedidos: int
    total_ventas: Decimal


class ProductoMasVendidoOut(OrmModel):
    producto_id: int
    nombre: str
    tipo_producto: str
    cantidad_vendida: Decimal
    total_ventas: Decimal


class UtilidadProductoOut(OrmModel):
    producto_id: int
    nombre: str
    tipo_producto: str
    ingreso: Decimal
    costo_estimado: Decimal
    utilidad: Decimal
    margen_porcentaje: Decimal


class RentabilidadPedidoOut(OrmModel):
    pedido_id: int
    numero_pedido: str
    cliente_id: int
    fecha_pedido: str | None
    ingreso: Decimal
    costo_estimado: Decimal
    utilidad: Decimal
    margen_porcentaje: Decimal


class CostoProduccionOut(OrmModel):
    etapa_costo: str
    tipo_costo: str
    categoria: str
    total: Decimal
    cantidad_asientos: int


class CostoCategoriaOut(OrmModel):
    tipo_costo: str
    total: Decimal


class CompraReporteOut(OrmModel):
    compra_id: int
    proveedor_id: int
    numero_factura: str | None
    fecha_compra: str | None
    estado: str
    subtotal: Decimal
    total: Decimal


class GastoReporteOut(OrmModel):
    gasto_id: int
    categoria: str
    descripcion: str
    monto: Decimal
    fecha_gasto: str | None
    estado_pago: str


class InventarioValorizadoOut(OrmModel):
    existencia_id: int
    bodega_id: int
    bodega: str
    tipo_articulo: str
    articulo_id: int
    articulo: str
    cantidad: Decimal
    costo_unitario: Decimal
    valor_total: Decimal


class ConsumoMaterialOut(OrmModel):
    material_id: int
    nombre: str
    cantidad_consumida: Decimal
    cantidad_desperdicio: Decimal
    costo_total: Decimal


class DesperdicioOut(OrmModel):
    consumo_id: int
    material_id: int
    material: str
    cantidad: Decimal
    costo_unitario: Decimal
    costo_total: Decimal
    consumido_en: str | None
    notas: str | None


class CuentasPendientesOut(OrmModel):
    cuentas_por_cobrar: list[CuentaPorCobrarOut]
    cuentas_por_pagar: list[CuentaPorPagarOut]
    total_cxc: Decimal
    total_cxp: Decimal


class EvolucionRentabilidadOut(OrmModel):
    periodo: str
    ventas: Decimal
    costos: Decimal
    gastos: Decimal
    utilidad: Decimal


class DashboardOut(OrmModel):
    """KPIs del dashboard — agregación real (§5.10)."""

    ventas_dia: Decimal
    ventas_mes: Decimal
    dinero_recibido: Decimal
    pedidos_pendientes: int = Field(
        description="Pedidos en PENDIENTE/CONFIRMADO/DISENO/ESPERANDO_APROBACION"
    )
    pedidos_en_produccion: int
    pedidos_listos: int
    cuentas_por_cobrar: Decimal
    gastos_mes: Decimal
    utilidad_estimada: Decimal
    stock_bajo: int
    costos_produccion: Decimal
    utilidad_operativa: Decimal
    ingresos_vs_gastos: list[EvolucionRentabilidadOut]
    ventas_por_dia: list[VentaDiariaOut]
    productos_mas_vendidos: list[ProductoMasVendidoOut]
    costos_por_categoria: list[CostoCategoriaOut]
    notas: str
