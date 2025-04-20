# app/schemas/schema_producto.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# Forward declaration para evitar importación circular con Presentacion
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .schema_presentacion import Presentacion

class ProductoBase(BaseModel):
    nombre: str = Field(..., max_length=255)
    descripcion: Optional[str] = None
    precio_compra: Decimal = Field(..., gt=0, decimal_places=2)
    activo: bool = True

class ProductoCreate(ProductoBase):
    pass

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=255)
    descripcion: Optional[str] = None
    precio_compra: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    activo: Optional[bool] = None

class Producto(ProductoBase):
    id: int
    created_at: datetime
    # Incluir presentaciones al leer un producto
    presentaciones: List["Presentacion"] = [] # Usar string para forward ref

    class Config:
        from_attributes = True