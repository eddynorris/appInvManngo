# app/schemas/schema_proveedor.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ProveedorBase(BaseModel):
    nombre: str = Field(..., max_length=255)
    telefono: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = None

class ProveedorCreate(ProveedorBase):
    pass

class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=255)
    telefono: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = None

class Proveedor(ProveedorBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True