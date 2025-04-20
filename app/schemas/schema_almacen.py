# app/schemas/schema_almacen.py
from pydantic import BaseModel, Field
from typing import Optional

class AlmacenBase(BaseModel):
    nombre: str = Field(..., max_length=255)
    direccion: Optional[str] = None
    ciudad: Optional[str] = Field(None, max_length=100)

class AlmacenCreate(AlmacenBase):
    pass

class AlmacenUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=255)
    direccion: Optional[str] = None
    ciudad: Optional[str] = Field(None, max_length=100)

class Almacen(AlmacenBase):
    id: int

    class Config:
        from_attributes = True