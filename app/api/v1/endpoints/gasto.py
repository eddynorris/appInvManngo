# app/api/v1/endpoints/gasto.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional
from datetime import date
from app import crud, models, schemas
from app.api import deps
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Users


logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[schemas.Gasto])
def read_gastos(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=200),
    almacen_id: int | None = Query(default=None),
    categoria: str | None = Query(default=None),
    usuario_id: int | None = Query(default=None),
    fecha_inicio: Optional[date] = Query(default=None),
    fecha_fin: Optional[date] = Query(default=None),
    current_user: "Users" = Depends(deps.get_current_active_user),
) -> Any:
    """Recupera lista de gastos con filtros opcionales."""
    # Aplicar filtro de almacén si el usuario no es admin
    query_almacen_id = almacen_id
    if current_user.rol != 'admin':
        if query_almacen_id is None:
            query_almacen_id = current_user.almacen_id
        elif query_almacen_id != current_user.almacen_id:
             return [] # O 403

    filters = {
        "almacen_id": query_almacen_id,
        "categoria": categoria,
        "usuario_id": usuario_id,
        "fecha_inicio": fecha_inicio, # CRUD necesita manejar filtro de fecha
        "fecha_fin": fecha_fin,       # CRUD necesita manejar filtro de fecha
    }
    active_filters = {k: v for k, v in filters.items() if v is not None}

    gastos = crud.crud_gasto.get_gastos(db, skip=skip, limit=limit, **active_filters)
    return gastos

@router.post("/", response_model=schemas.Gasto, status_code=status.HTTP_201_CREATED)
def create_gasto(
    *,
    db: Session = Depends(deps.get_db),
    gasto_in: schemas.GastoCreate,
    current_user: "Users" = Depends(deps.get_current_active_user), # Quién registra
) -> Any:
    """Registra un nuevo gasto."""
    # Verificar permiso de almacén si se especifica
    if gasto_in.almacen_id:
        deps.get_verified_almacen(gasto_in.almacen_id, current_user)
    elif current_user.rol != 'admin':
        # Si no es admin y no especifica almacén, asignar el suyo
        gasto_in.almacen_id = current_user.almacen_id

    gasto = crud.crud_gasto.create_gasto(db=db, gasto=gasto_in, usuario_id=current_user.id)
    return gasto

@router.get("/{gasto_id}", response_model=schemas.Gasto)
def read_gasto_by_id(
    gasto_id: int,
    db: Session = Depends(deps.get_db),
    current_user: "Users" = Depends(deps.get_current_active_user),
) -> Any:
    """Obtiene un gasto por ID."""
    gasto = crud.crud_gasto.get_gasto(db, gasto_id=gasto_id)
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    # Verificar permiso de almacén si el gasto tiene uno asignado
    if gasto.almacen_id:
        deps.get_verified_almacen(gasto.almacen_id, current_user)
    elif current_user.rol != 'admin':
         # Si el gasto no tiene almacén y el usuario no es admin, ¿puede verlo?
         # Asumimos que sí por ahora, ajustar si es necesario.
         pass
    return gasto

@router.put("/{gasto_id}", response_model=schemas.Gasto)
def update_gasto(
    *,
    db: Session = Depends(deps.get_db),
    gasto_id: int,
    gasto_in: schemas.GastoUpdate,
    current_user: "Users" = Depends(deps.get_current_active_user), # O rol específico
) -> Any:
    """Actualiza un gasto."""
    gasto = crud.crud_gasto.get_gasto(db, gasto_id=gasto_id)
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    # Verificar permiso sobre el almacén original del gasto
    if gasto.almacen_id:
        deps.get_verified_almacen(gasto.almacen_id, current_user)
    # Verificar permiso sobre el NUEVO almacén si se intenta cambiar
    update_data = gasto_in.model_dump(exclude_unset=True)
    if "almacen_id" in update_data and update_data["almacen_id"] is not None:
         deps.get_verified_almacen(update_data["almacen_id"], current_user)

    updated_gasto = crud.crud_gasto.update_gasto(db=db, db_obj=gasto, obj_in=gasto_in)
    return updated_gasto

@router.delete("/{gasto_id}", response_model=schemas.Gasto)
def delete_gasto(
    *,
    db: Session = Depends(deps.get_db),
    gasto_id: int,
    current_user: "Users" = Depends(deps.require_rol('admin', 'gerente')), # Ejemplo
) -> Any:
    """Elimina un gasto."""
    gasto = crud.crud_gasto.get_gasto(db, gasto_id=gasto_id)
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    # Verificar permiso de almacén
    if gasto.almacen_id:
        deps.get_verified_almacen(gasto.almacen_id, current_user)

    deleted_gasto = crud.crud_gasto.delete_gasto(db=db, gasto_id=gasto_id)
    return deleted_gasto