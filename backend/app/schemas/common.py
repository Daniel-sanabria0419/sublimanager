"""Schemas compartidos."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MensajeOut(BaseModel):
    detalle: str


class PaginacionParams(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=500)


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
