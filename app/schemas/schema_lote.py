# app/schemas/schema_lote.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from .schema_proveedor import Proveedor # Para anidar
from .schema_producto import ProductoBase # Para anidar info básica

class LoteBase(BaseModel):
    producto_id: int
    proveedor_id: Optional[int] = None
    peso_humedo_kg: Decimal = Field(..., gt=0, decimal_places=2)
    peso_seco_kg: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    cantidad_disponible_kg: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    # fecha_ingreso se establece por defecto en la BD

class LoteCreate(LoteBase):
    # Al crear, la cantidad disponible usualmente es el peso húmedo o seco
    cantidad_disponible_kg: Optional[Decimal] = Field(None, ge=0, decimal_places=2)

class LoteUpdate(BaseModel):
    # Permitir actualizar proveedor, pesos, cantidad disponible
    proveedor_id: Optional[int] = None
    peso_humedo_kg: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    peso_seco_kg: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    cantidad_disponible_kg: Optional[Decimal] = Field(None, ge=0, decimal_places=2)

class Lote(LoteBase):
    id: int
    fecha_ingreso: datetime
    # Anidar información relevante
    proveedor: Optional[Proveedor] = None
    producto: Optional[ProductoBase] = None # Solo info básica

    class Config:
        from_attributes = True