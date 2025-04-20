# app/schemas/schema_presentacion.py
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from .schema_producto import ProductoBase # Importar solo lo necesario

class PresentacionBase(BaseModel):
    producto_id: int
    nombre: str = Field(..., max_length=100)
    capacidad_kg: Decimal = Field(..., gt=0, decimal_places=2)
    # Validar tipo con Literal o Enum sería más robusto
    tipo: str = Field(..., pattern="^(bruto|procesado|merma|briqueta|detalle)$")
    precio_venta: Decimal = Field(..., gt=0, decimal_places=2)
    activo: bool = True
    url_foto: Optional[str] = Field(None, max_length=255)

class PresentacionCreate(PresentacionBase):
    pass

class PresentacionUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=100)
    capacidad_kg: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    tipo: Optional[str] = Field(None, pattern="^(bruto|procesado|merma|briqueta|detalle)$")
    precio_venta: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    activo: Optional[bool] = None
    url_foto: Optional[str] = Field(None, max_length=255)
    # No permitir cambiar producto_id en update

# Esquema para leer (incluye info del producto)
class Presentacion(PresentacionBase):
    id: int
    # Anidar info básica del producto
    producto: Optional[ProductoBase] = None # Anidar info básica

    class Config:
        from_attributes = True

# Actualizar la forward reference en Producto
from .schema_producto import Producto
Producto.model_rebuild()