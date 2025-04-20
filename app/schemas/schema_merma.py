# app/schemas/schema_merma.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from .schema_lote import Lote # Para anidar info básica
from .schema_user import UserBase # Para anidar info básica

class MermaBase(BaseModel):
    lote_id: int
    cantidad_kg: Decimal = Field(..., gt=0, decimal_places=2)
    convertido_a_briquetas: bool = False
    usuario_id: Optional[int] = None
    # fecha_registro se establece por defecto

class MermaCreate(MermaBase):
    pass

class MermaUpdate(BaseModel):
    # Usualmente solo se actualiza si se convirtió
    convertido_a_briquetas: Optional[bool] = None
    # No permitir cambiar lote_id, cantidad, usuario en update típico

class Merma(MermaBase):
    id: int
    fecha_registro: datetime
    # Anidar información relevante
    lote: Optional[Lote] = None # Podría ser solo LoteBase si es mucha info
    usuario: Optional[UserBase] = None # Solo info básica

    class Config:
        from_attributes = True