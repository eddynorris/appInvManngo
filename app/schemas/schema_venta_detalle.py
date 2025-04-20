# app/schemas/schema_venta_detalle.py
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from .schema_presentacion import Presentacion # Para anidar info
from typing import TYPE_CHECKING


class VentaDetalleBase(BaseModel):
    presentacion_id: int
    cantidad: int = Field(..., gt=0)
    precio_unitario: Decimal = Field(..., gt=0, decimal_places=2)
    # venta_id se asigna al crear la venta completa

class VentaDetalleCreate(VentaDetalleBase):
    pass

class VentaDetalleUpdate(BaseModel):
    # Qué permitir actualizar? Cantidad? Precio?
    cantidad: Optional[int] = Field(None, gt=0)
    precio_unitario: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    # No permitir cambiar presentacion_id

class VentaDetalle(VentaDetalleBase):
    id: int
    # Anidar info de presentación
    presentacion: Optional[Presentacion] = None
    # Podría calcular total_linea aquí si no está en el modelo
    total_linea: Optional[Decimal] = None # Calcular en el endpoint

    class Config:
        from_attributes = True