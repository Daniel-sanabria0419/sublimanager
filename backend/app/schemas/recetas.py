"""Schemas Pydantic del módulo recetas y costos (campos en español)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field, field_validator

from app.models.enums import TipoCosto
from app.schemas.common import OrmModel
from app.utils.decimal_policy import a_decimal, money_round, percent_round, qty_round


class CategoriaCostoCreate(OrmModel):
    nombre: str = Field(min_length=1, max_length=120)
    tipo_costo: TipoCosto
    activo: bool = True


class CategoriaCostoUpdate(OrmModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    tipo_costo: TipoCosto | None = None
    activo: bool | None = None


class CategoriaCostoOut(OrmModel):
    id: int
    nombre: str
    tipo_costo: str
    activo: bool


class ItemRecetaCreate(OrmModel):
    material_id: int
    cantidad: Decimal
    porcentaje_desperdicio: Decimal = Decimal("0")
    notas: str | None = None

    @field_validator("cantidad", mode="before")
    @classmethod
    def _qty(cls, v):  # noqa: ANN001
        return qty_round(a_decimal(v))

    @field_validator("porcentaje_desperdicio", mode="before")
    @classmethod
    def _pct(cls, v):  # noqa: ANN001
        return percent_round(a_decimal(v))


class ItemRecetaOut(OrmModel):
    id: int
    receta_id: int
    material_id: int
    cantidad: Decimal
    porcentaje_desperdicio: Decimal
    notas: str | None


class RecetaProductoCreate(OrmModel):
    producto_id: int
    variante_id: int | None = None
    nombre: str = Field(min_length=1, max_length=120)
    activo: bool = True
    items: list[ItemRecetaCreate] = Field(default_factory=list)


class RecetaProductoOut(OrmModel):
    id: int
    producto_id: int
    variante_id: int | None
    version: int
    nombre: str
    activo: bool
    creado_en: datetime
    items: list[ItemRecetaOut] = Field(default_factory=list)


class PerfilCostoProductoCreate(OrmModel):
    producto_id: int
    variante_id: int | None = None
    costo_mano_obra_por_unidad: Decimal = Decimal("0")
    costo_electricidad_por_unidad: Decimal = Decimal("0")
    costo_depreciacion_por_unidad: Decimal = Decimal("0")
    costo_otros_por_unidad: Decimal = Decimal("0")
    vigente_desde: datetime | None = None
    activo: bool = True

    @field_validator(
        "costo_mano_obra_por_unidad",
        "costo_electricidad_por_unidad",
        "costo_depreciacion_por_unidad",
        "costo_otros_por_unidad",
        mode="before",
    )
    @classmethod
    def _money(cls, v):  # noqa: ANN001
        return money_round(a_decimal(v))


class PerfilCostoProductoOut(OrmModel):
    id: int
    producto_id: int
    variante_id: int | None
    costo_mano_obra_por_unidad: Decimal
    costo_electricidad_por_unidad: Decimal
    costo_depreciacion_por_unidad: Decimal
    costo_otros_por_unidad: Decimal
    vigente_desde: datetime
    activo: bool


class CostoEstimadoOut(OrmModel):
    producto_id: int
    variante_id: int | None
    tipo_producto: str
    costo_materiales: Decimal
    costo_mano_obra: Decimal
    costo_electricidad: Decimal
    costo_depreciacion: Decimal
    costo_otros: Decimal
    costo_estimado: Decimal
    precio_venta: Decimal | None = None
    utilidad: Decimal | None = None
    margen_porcentaje: Decimal | None = None
    receta_id: int | None = None
    receta_version: int | None = None
    perfil_costo_id: int | None = None
