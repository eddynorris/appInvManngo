# app/schemas/schema_venta.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from .schema_cliente import Cliente # Anidar
from .schema_almacen import Almacen # Anidar
from .schema_user import UserBase # Anidar vendedor
from .schema_venta_detalle import VentaDetalle, VentaDetalleCreate, VentaDetalleUpdate

class VentaBase(BaseModel):
    cliente_id: int
    almacen_id: int
    vendedor_id: Optional[int] = None # Asignar al crear
    # fecha se asigna al crear
    total: Decimal = Field(..., ge=0, decimal_places=2) # ge=0 si puede haber ventas de 0?
    tipo_pago: str = Field(..., pattern="^(contado|credito)$")
    estado_pago: str = Field(default='pendiente', pattern="^(pendiente|parcial|pagado)$")
    consumo_diario_kg: Optional[Decimal] = Field(None, gt=0, decimal_places=2)

class VentaCreate(VentaBase):
    # Al crear, se reciben los detalles
    detalles: List[VentaDetalleCreate] = []
    # Quitar campos que se calculan o asignan al crear
    total: Optional[Decimal] = Field(None, description="Se calculará a partir de los detalles")
    vendedor_id: Optional[int] = Field(None, description="Se asignará desde el token JWT")
    estado_pago: Optional[str] = Field(default='pendiente')


class VentaUpdate(BaseModel):
    # Qué se puede actualizar? Tipo/Estado pago? Consumo?
    tipo_pago: Optional[str] = Field(None, pattern="^(contado|credito)$")
    estado_pago: Optional[str] = Field(None, pattern="^(pendiente|parcial|pagado)$")
    consumo_diario_kg: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    # Actualizar detalles requeriría lógica compleja (mejor no permitir o endpoint específico)
    # detalles: Optional[List[VentaDetalleUpdate]] = None # Evitar por complejidad
    # No permitir cambiar cliente, almacen, vendedor, total directamente

class Venta(VentaBase):
    id: int
    fecha: datetime
    # Anidar información completa
    cliente: Optional[Cliente] = None
    almacen: Optional[Almacen] = None
    vendedor: Optional[UserBase] = None
    detalles: List[VentaDetalle] = []
    # Incluir saldo pendiente calculado
    saldo_pendiente: Optional[Decimal] = None # Calcular en endpoint

    class Config:
        from_attributes = True