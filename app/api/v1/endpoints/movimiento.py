# app/api/v1/endpoints/movimiento.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional
from app import crud, models, schemas
from app.api import deps
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Users


logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[schemas.Movimiento])
def read_movimientos(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=500), # Permitir ver más historial?
    presentacion_id: int | None = Query(default=None),
    lote_id: int | None = Query(default=None),
    tipo: str | None = Query(default=None, pattern="^(entrada|salida)$"),
    # Añadir filtros por fecha, usuario, almacén (requiere join o info en movimiento)
    current_user: "Users" = Depends(deps.get_current_active_user),
) -> Any:
    """Recupera lista de movimientos."""
    # Añadir lógica de autorización (ej: solo movimientos de su almacén)
    filters = {
        "presentacion_id": presentacion_id,
        "lote_id": lote_id,
        "tipo": tipo,
    }
    active_filters = {k: v for k, v in filters.items() if v is not None}
    movimientos = crud.crud_movimiento.get_movimientos(db, skip=skip, limit=limit, **active_filters)
    return movimientos

@router.get("/{movimiento_id}", response_model=schemas.Movimiento)
def read_movimiento_by_id(
    movimiento_id: int,
    db: Session = Depends(deps.get_db),
    current_user: "Users" = Depends(deps.get_current_active_user),
) -> Any:
    """Obtiene un movimiento por ID."""
    movimiento = crud.crud_movimiento.get_movimiento(db, movimiento_id=movimiento_id)
    if not movimiento:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    # Añadir lógica de autorización (ej: almacén)
    return movimiento

# POST, PUT, DELETE para Movimiento usualmente no se exponen directamente,
# se crean/eliminan como efecto secundario de otras operaciones (Venta, Ajuste, Merma).