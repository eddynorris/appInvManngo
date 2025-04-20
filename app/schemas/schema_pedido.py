# app/schemas/schema_pedido.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from .schema_cliente import Cliente # Anidar
from .schema_almacen import Almacen # Anidar
from .schema_user import UserBase # Anidar vendedor
from .schema_pedido_detalle import PedidoDetalle, PedidoDetalleCreate, PedidoDetalleUpdate

class PedidoBase(BaseModel):
    cliente_id: int
    almacen_id: int
    vendedor_id: Optional[int] = None # Quién tomó el pedido
    fecha_entrega: datetime # Fecha/hora requerida
    estado: str = Field(default='programado', pattern="^(programado|confirmado|entregado|cancelado)$")
    notas: Optional[str] = None
    # fecha_creacion se establece por defecto

class PedidoCreate(PedidoBase):
    detalles: List[PedidoDetalleCreate] = []
    vendedor_id: Optional[int] = Field(None, description="Se asignará desde el token JWT")

class PedidoUpdate(BaseModel):
    fecha_entrega: Optional[datetime] = None
    estado: Optional[str] = Field(None, pattern="^(programado|confirmado|entregado|cancelado)$")
    notas: Optional[str] = None
    # Actualizar detalles requeriría lógica compleja, evitar aquí
    # detalles: Optional[List[PedidoDetalleUpdate]] = None
    # No permitir cambiar cliente, almacen, vendedor

class Pedido(PedidoBase):
    id: int
    fecha_creacion: datetime
    # Anidar información
    cliente: Optional[Cliente] = None
    almacen: Optional[Almacen] = None
    vendedor: Optional[UserBase] = None
    detalles: List[PedidoDetalle] = []
    # Calcular total_estimado
    total_estimado: Optional[Decimal] = None # Calcular en endpoint

    class Config:
        from_attributes = True