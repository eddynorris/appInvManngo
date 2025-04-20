# app/api/v1/endpoints/lote.py
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

@router.get("/", response_model=List[schemas.Lote])
def read_lotes(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=200),
    producto_id: int | None = Query(default=None),
    proveedor_id: int | None = Query(default=None),
    current_user: "Users" = Depends(deps.get_current_active_user), # ¿Necesita autorización?
) -> Any:
    """Recupera lista de lotes."""
    # Añadir lógica de autorización si solo ciertos usuarios pueden ver lotes
    lotes = crud.crud_lote.get_lotes(db, skip=skip, limit=limit, producto_id=producto_id, proveedor_id=proveedor_id)
    return lotes

@router.post("/", response_model=schemas.Lote, status_code=status.HTTP_201_CREATED)
def create_lote(
    *,
    db: Session = Depends(deps.get_db),
    lote_in: schemas.LoteCreate,
    current_user: "Users" = Depends(deps.require_rol('admin', 'gerente')), # Ejemplo
) -> Any:
    """Registra un nuevo lote."""
    # Validar existencia de producto y proveedor si se proporcionan
    if not crud.crud_producto.get_producto(db, lote_in.producto_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Producto ID {lote_in.producto_id} no encontrado.")
    if lote_in.proveedor_id and not crud.crud_proveedor.get_proveedor(db, lote_in.proveedor_id):
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Proveedor ID {lote_in.proveedor_id} no encontrado.")

    lote = crud.crud_lote.create_lote(db=db, lote=lote_in)
    return lote

@router.get("/{lote_id}", response_model=schemas.Lote)
def read_lote_by_id(
    lote_id: int,
    db: Session = Depends(deps.get_db),
    current_user: "Users" = Depends(deps.get_current_active_user), # ¿Autorización?
) -> Any:
    """Obtiene un lote por ID."""
    lote = crud.crud_lote.get_lote(db, lote_id=lote_id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    return lote

@router.put("/{lote_id}", response_model=schemas.Lote)
def update_lote(
    *,
    db: Session = Depends(deps.get_db),
    lote_id: int,
    lote_in: schemas.LoteUpdate,
    current_user: "Users" = Depends(deps.require_rol('admin', 'gerente')), # Ejemplo
) -> Any:
    """Actualiza un lote."""
    lote = crud.crud_lote.get_lote(db, lote_id=lote_id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    # Validar proveedor si se cambia
    update_data = lote_in.model_dump(exclude_unset=True)
    if "proveedor_id" in update_data and update_data["proveedor_id"]:
         if not crud.crud_proveedor.get_proveedor(db, update_data["proveedor_id"]):
              raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Proveedor ID {update_data['proveedor_id']} no encontrado.")

    updated_lote = crud.crud_lote.update_lote(db=db, db_obj=lote, obj_in=lote_in)
    return updated_lote

@router.delete("/{lote_id}", response_model=schemas.Lote)
def delete_lote(
    *,
    db: Session = Depends(deps.get_db),
    lote_id: int,
    current_user: "Users" = Depends(deps.require_admin), # Ejemplo
) -> Any:
    """Elimina un lote."""
    lote = crud.crud_lote.get_lote(db, lote_id=lote_id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    # Considerar si hay inventario/mermas/movimientos asociados (SET NULL?)
    deleted_lote = crud.crud_lote.delete_lote(db=db, lote_id=lote_id)
    return deleted_lote