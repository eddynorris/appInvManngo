# app/schemas/schema_gasto.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date # Gasto usa DATE
from decimal import Decimal
from .schema_almacen import Almacen # Anidar
from .schema_user import UserBase # Anidar

class GastoBase(BaseModel):
    descripcion: str
    monto: Decimal = Field(..., gt=0, decimal_places=2)
    fecha: date = Field(default_factory=date.today) # Default a hoy si no se provee
    categoria: str = Field(..., pattern="^(logistica|personal|otros)$")
    almacen_id: Optional[int] = None
    usuario_id: Optional[int] = None # Quién registró

class GastoCreate(GastoBase):
    pass

class GastoUpdate(BaseModel):
    descripcion: Optional[str] = None
    monto: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    fecha: Optional[date] = None
    categoria: Optional[str] = Field(None, pattern="^(logistica|personal|otros)$")
    almacen_id: Optional[int] = None # Permitir cambiar almacén?
    # No permitir cambiar usuario

class Gasto(GastoBase):
    id: int
    # Anidar info
    almacen: Optional[Almacen] = None
    usuario: Optional[UserBase] = None

    class Config:
        from_attributes = True