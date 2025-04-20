# app/schemas/schema_movimiento.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from .schema_presentacion import Presentacion # Anidar
from .schema_lote import Lote # Anidar info básica
from .schema_user import UserBase # Anidar info básica

class MovimientoBase(BaseModel):
    # Validar tipo con Literal o Enum sería más robusto
    tipo: str = Field(..., pattern="^(entrada|salida)$")
    presentacion_id: int
    lote_id: Optional[int] = None
    usuario_id: Optional[int] = None # Quién registró el movimiento
    cantidad: Decimal = Field(..., gt=0, decimal_places=2)
    motivo: Optional[str] = Field(None, max_length=255)
    # fecha se establece por defecto

class MovimientoCreate(MovimientoBase):
    pass

# Los movimientos usualmente no se actualizan, se crean nuevos
# o se crean movimientos de reversión. No definir MovimientoUpdate.

class Movimiento(MovimientoBase):
    id: int
    fecha: datetime
    # Anidar información relevante
    presentacion: Optional[Presentacion] = None
    lote: Optional[Lote] = None # Podría ser LoteBase
    usuario: Optional[UserBase] = None

    class Config:
        from_attributes = True