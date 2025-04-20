    # app/api/v1/endpoints/almacen.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, TYPE_CHECKING
from app import crud, models, schemas
from app.api import deps

# Definir el tipo dentro de TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.models import Users # Ajusta la ruta si es necesario

router = APIRouter()
@router.get("/", response_model=List[schemas.Almacen])
def read_almacenes(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=200),
    current_user: "Users" = Depends(deps.get_current_active_user), # ¿O solo admin?
) -> Any:
    """Recupera lista de almacenes."""
    # Aplicar filtro si el usuario no es admin?
    # if current_user.rol != 'admin':
    #     almacen = crud.crud_almacen.get_almacen(db, current_user.almacen_id)
    #     return [almacen] if almacen else []
    almacenes = crud.crud_almacen.get_almacenes(db, skip=skip, limit=limit)
    return almacenes
@router.post("/", response_model=schemas.Almacen, status_code=status.HTTP_201_CREATED)
def create_almacen(
    *,
    db: Session = Depends(deps.get_db),
    almacen_in: schemas.AlmacenCreate,
    current_user: "Users" = Depends(deps.require_admin), # Solo admin crea almacenes
) -> Any:
    """Crea un nuevo almacén."""
    almacen = crud.crud_almacen.create_almacen(db=db, almacen=almacen_in)
    return almacen
@router.get("/{almacen_id}", response_model=schemas.Almacen)
def read_almacen_by_id(
    almacen_id: int,
    db: Session = Depends(deps.get_db),
    current_user: "Users" = Depends(deps.get_current_active_user),
) -> Any:
    """Obtiene un almacén por ID."""
    # Verificar acceso al almacén
    try:
        deps.get_verified_almacen(almacen_id, current_user)
    except HTTPException as e:
         raise e # Re-lanzar 403
    almacen = crud.crud_almacen.get_almacen(db, almacen_id=almacen_id)
    if not almacen:
        raise HTTPException(status_code=404, detail="Almacén no encontrado")
    return almacen
@router.put("/{almacen_id}", response_model=schemas.Almacen)
def update_almacen(
    *,
    db: Session = Depends(deps.get_db),
    almacen_id: int,
    almacen_in: schemas.AlmacenUpdate,
    current_user: "Users" = Depends(deps.require_admin), # Solo admin modifica
) -> Any:
    """Actualiza un almacén."""
    almacen = crud.crud_almacen.get_almacen(db, almacen_id=almacen_id)
    if not almacen:
        raise HTTPException(status_code=404, detail="Almacén no encontrado")
    almacen = crud.crud_almacen.update_almacen(db=db, db_obj=almacen, obj_in=almacen_in)
    return almacen
@router.delete("/{almacen_id}", response_model=schemas.Almacen)
def delete_almacen(
    *,
    db: Session = Depends(deps.get_db),
    almacen_id: int,
    current_user: "Users" = Depends(deps.require_admin), # Solo admin elimina
) -> Any:
    """Elimina un almacén."""
    almacen = crud.crud_almacen.get_almacen(db, almacen_id=almacen_id)
    if not almacen:
        raise HTTPException(status_code=404, detail="Almacén no encontrado")
    # Añadir lógica si no se puede eliminar (ej: tiene inventario)
    deleted_almacen = crud.crud_almacen.delete_almacen(db=db, almacen_id=almacen_id)
    return deleted_almacen