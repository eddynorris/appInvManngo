# app/schemas/schema_inventario.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .schema_presentacion import Presentacion # Para anidar
from .schema_almacen import Almacen # Para anidar
from .schema_lote import Lote # Para anidar info básica

class InventarioBase(BaseModel):
    presentacion_id: int
    almacen_id: int
    lote_id: Optional[int] = None # Puede no estar asociado a un lote específico
    cantidad: int = Field(..., ge=0)
    stock_minimo: int = Field(default=10, ge=0)
    # ultima_actualizacion se establece por defecto

class InventarioCreate(InventarioBase):
    pass # Permitir establecer cantidad inicial

class InventarioUpdate(BaseModel):
    # Usualmente solo se actualiza cantidad o stock_minimo
    cantidad: Optional[int] = Field(None, ge=0)
    stock_minimo: Optional[int] = Field(None, ge=0)
    lote_id: Optional[int] = None # Permitir reasignar lote si es necesario
    # No permitir cambiar presentacion_id o almacen_id en update

class Inventario(InventarioBase):
    id: int
    ultima_actualizacion: datetime
    # Anidar información completa o parcial
    presentacion: Optional[Presentacion] = None
    almacen: Optional[Almacen] = None
    lote: Optional[Lote] = None # Podría ser solo LoteBase

    class Config:
        from_attributes = True