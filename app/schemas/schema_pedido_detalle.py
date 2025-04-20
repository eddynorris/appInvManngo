# app/schemas/schema_pedido_detalle.py
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from .schema_presentacion import Presentacion # Anidar

class PedidoDetalleBase(BaseModel):
    presentacion_id: int
    cantidad: int = Field(..., gt=0)
    precio_estimado: Decimal = Field(..., ge=0, decimal_places=2) # Estimado puede ser 0?
    # pedido_id se asigna al crear pedido

class PedidoDetalleCreate(PedidoDetalleBase):
    pass

class PedidoDetalleUpdate(BaseModel):
    cantidad: Optional[int] = Field(None, gt=0)
    precio_estimado: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    # No permitir cambiar presentacion_id

class PedidoDetalle(PedidoDetalleBase):
    id: int
    presentacion: Optional[Presentacion] = None

    class Config:
        from_attributes = True