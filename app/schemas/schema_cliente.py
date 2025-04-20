from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal

# Esquema base con campos comunes
class ClienteBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)
    telefono: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = None
    frecuencia_compra_dias: Optional[int] = Field(None, gt=0)
    ultima_fecha_compra: Optional[date] = None # Usar date si no necesitas la hora

# Esquema para crear un cliente (campos necesarios en el request body)
class ClienteCreate(ClienteBase):
    pass # Hereda todos los campos de ClienteBase

# Esquema para actualizar un cliente (todos los campos son opcionales)
class ClienteUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    telefono: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = None
    frecuencia_compra_dias: Optional[int] = Field(None, gt=0)
    ultima_fecha_compra: Optional[date] = None

# Esquema para leer/retornar un cliente (incluye campos de la BD como id, created_at)
class Cliente(ClienteBase):
    id: int
    created_at: datetime
    # Si quieres incluir el saldo pendiente (calculado), añádelo aquí
    # Puede que necesites calcularlo en el endpoint antes de retornar
    saldo_pendiente: Optional[Decimal] = None # Ejemplo

    class Config:
        from_attributes = True # Permite cargar datos desde objetos SQLAlchemy (nuevo en Pydantic v2)
        # orm_mode = True # (Para Pydantic v1)
