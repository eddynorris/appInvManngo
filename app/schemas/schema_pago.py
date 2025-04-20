# app/schemas/schema_pago.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
# from .schema_venta import Venta # Evitar anidación profunda, usar solo ID?
from .schema_user import UserBase # Anidar info básica

class PagoBase(BaseModel):
    venta_id: int
    monto: Decimal = Field(..., gt=0, decimal_places=2)
    metodo_pago: str = Field(..., pattern="^(efectivo|transferencia|tarjeta)$")
    referencia: Optional[str] = Field(None, max_length=50)
    usuario_id: Optional[int] = None # Quién registró el pago
    url_comprobante: Optional[str] = Field(None, max_length=255)
    # fecha se establece por defecto

class PagoCreate(PagoBase):
    pass

class PagoUpdate(BaseModel):
    # Qué permitir actualizar? Referencia? Comprobante?
    referencia: Optional[str] = Field(None, max_length=50)
    url_comprobante: Optional[str] = Field(None, max_length=255)
    # No permitir cambiar venta_id, monto, metodo, usuario

class Pago(PagoBase):
    id: int
    fecha: datetime
    # Anidar info relevante
    # venta: Optional[Venta] = None # Podría ser mucho, quizás solo IDs
    usuario: Optional[UserBase] = None

    class Config:
        from_attributes = True