"""CajaService — movimientos de caja, CxC/CxP y resumen financiero (§5.10).

Los movimientos se generan automáticamente al confirmar pagos; este service
es de consulta (no crea movimientos manuales en V1 Stage 7).

Diferenciación §5.10:
- Ventas = pedidos ENTREGADOS (no anticipos)
- Caja = movimientos_caja / saldos de cuentas
- Costos = asientos REAL de producción
- Gastos = gastos operativos (excluye ligados a OP vía gasto_id y ≠ compras)
- Utilidad bruta = ventas − costos
- Utilidad operativa = utilidad bruta − gastos operativos
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import EstadoPago
from app.models.finanzas.movimientos_caja import MovimientoCaja
from app.models.finanzas.pagos_proveedor import PagoProveedor
from app.repositories.finanzas import (
    ConsultasFinancierasRepo,
    CuentaCajaRepo,
    GastoRepo,
    MovimientoCajaRepo,
)
from app.utils.decimal_policy import money_round


class CajaService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.movimientos = MovimientoCajaRepo(db)
        self.cuentas = CuentaCajaRepo(db)
        self.gastos = GastoRepo(db)
        self.consultas = ConsultasFinancierasRepo(db)

    def listar_movimientos(
        self,
        *,
        cuenta_caja_id: int | None = None,
        tipo_movimiento: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[MovimientoCaja]:
        if cuenta_caja_id is not None:
            self.cuentas.obtener_o_404(cuenta_caja_id, "cuenta_caja")
        return self.movimientos.listar_filtrado(
            cuenta_caja_id=cuenta_caja_id,
            tipo_movimiento=tipo_movimiento,
            offset=offset,
            limit=limit,
        )

    def obtener_movimiento(self, id_: int) -> MovimientoCaja:
        return self.movimientos.obtener_o_404(id_, "movimiento_caja")

    def saldo_cuenta(self, cuenta_caja_id: int) -> dict:
        cuenta = self.cuentas.obtener_o_404(cuenta_caja_id, "cuenta_caja")
        saldo = money_round(self.movimientos.saldo_cuenta(cuenta_caja_id))
        return {
            "cuenta_caja_id": cuenta.id,
            "nombre": cuenta.nombre,
            "tipo_cuenta": cuenta.tipo_cuenta,
            "saldo": saldo,
        }

    def saldos_todas_las_cuentas(self) -> list[dict]:
        cuentas = self.cuentas.listar(offset=0, limit=500, filtros={"activo": True})
        return [self.saldo_cuenta(c.id) for c in cuentas]

    def cuentas_por_cobrar(self) -> list[dict]:
        filas = self.consultas.cuentas_por_cobrar()
        for f in filas:
            f["total"] = money_round(f["total"])
            f["total_pagado"] = money_round(f["total_pagado"])
            f["saldo_pendiente"] = money_round(f["saldo_pendiente"])
        return filas

    def cuentas_por_pagar(self) -> list[dict]:
        filas = self.consultas.cuentas_por_pagar()
        for f in filas:
            f["total"] = money_round(f["total"])
            f["total_pagado"] = money_round(f["total_pagado"])
            f["saldo_pendiente"] = money_round(f["saldo_pendiente"])
        return filas

    def resumen_financiero(self) -> dict:
        ventas = money_round(self.consultas.ventas_reconocidas())
        recibido = money_round(self.consultas.dinero_recibido_clientes())
        cxc = money_round(self.consultas.total_cxc())
        cxp = money_round(self.consultas.total_cxp())
        costos = money_round(self.consultas.costos_produccion_reales())
        # Gastos operativos: excluye los ya cargados a producción (electricidad etc.)
        gastos_op = money_round(self.gastos.suma_gastos_operativos_sin_produccion())
        # Pagos a proveedores CONFIRMADOS (caja, no gasto operativo)
        compras_pagadas = money_round(
            Decimal(
                str(
                    self.db.scalar(
                        select(func.coalesce(func.sum(PagoProveedor.monto), 0)).where(
                            PagoProveedor.estado == EstadoPago.CONFIRMADO
                        )
                    )
                    or 0
                )
            )
        )
        entradas, salidas = self.movimientos.totales_movimientos()
        entradas_m = money_round(entradas)
        salidas_m = money_round(salidas)
        utilidad_bruta = money_round(ventas - costos)
        utilidad_operativa = money_round(utilidad_bruta - gastos_op)

        return {
            "ventas_reconocidas": ventas,
            "dinero_recibido": recibido,
            "cuentas_por_cobrar": cxc,
            "costos_produccion": costos,
            "gastos_operativos": gastos_op,
            "compras_inventario_pagadas": compras_pagadas,
            "utilidad_bruta": utilidad_bruta,
            "utilidad_operativa": utilidad_operativa,
            "entradas_caja": entradas_m,
            "salidas_caja": salidas_m,
            "saldo_caja_neto": money_round(entradas_m - salidas_m),
            "cuentas_por_pagar": cxp,
            "notas": (
                "Ventas = pedidos ENTREGADOS. Dinero recibido = pagos CONFIRMADOS. "
                "Costos = asientos REAL de producción. "
                "Gastos operativos excluyen gastos ligados a OP (gasto_id) y "
                "compras de inventario (pagos_proveedor)."
            ),
        }
