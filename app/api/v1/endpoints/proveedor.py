# app/api/v1/endpoints/proveedor.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any
from app import crud, models, schemas
from app.api import deps
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Users


logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[schemas.Proveedor])
def read_proveedores(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=200),
    current_user: "Users" = Depends(deps.get_current_active_user), # Acceso restringido?
) -> Any:
    """Recupera lista de proveedores."""
    # Añadir lógica de autorización si es necesaria
    proveedores = crud.crud_proveedor.get_proveedores(db, skip=skip, limit=limit)
    return proveedores

@router.post("/", response_model=schemas.Proveedor, status_code=status.HTTP_201_CREATED)
def create_proveedor(
    *,
    db: Session = Depends(deps.get_db),
    proveedor_in: schemas.ProveedorCreate,
    current_user: "Users" = Depends(deps.require_rol('admin', 'gerente')), # Ejemplo
) -> Any:
    """Crea un nuevo proveedor."""
    existing_proveedor = db.query(models.Proveedor).filter(models.Proveedor.nombre == proveedor_in.nombre).first()
    if existing_proveedor:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Ya existe un proveedor con el nombre '{proveedor_in.nombre}'.")
    proveedor = crud.crud_proveedor.create_proveedor(db=db, proveedor=proveedor_in)
    return proveedor

@router.get("/{proveedor_id}", response_model=schemas.Proveedor)
def read_proveedor_by_id(
    proveedor_id: int,
    db: Session = Depends(deps.get_db),
    current_user: "Users" = Depends(deps.get_current_active_user), # Acceso restringido?
) -> Any:
    """Obtiene un proveedor por ID."""
    proveedor = crud.crud_proveedor.get_proveedor(db, proveedor_id=proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return proveedor

@router.put("/{proveedor_id}", response_model=schemas.Proveedor)
def update_proveedor(
    *,
    db: Session = Depends(deps.get_db),
    proveedor_id: int,
    proveedor_in: schemas.ProveedorUpdate,
    current_user: "Users" = Depends(deps.require_rol('admin', 'gerente')), # Ejemplo
) -> Any:
    """Actualiza un proveedor."""
    proveedor = crud.crud_proveedor.get_proveedor(db, proveedor_id=proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    update_data = proveedor_in.model_dump(exclude_unset=True)
    if "nombre" in update_data and update_data["nombre"] != proveedor.nombre:
         existing = db.query(models.Proveedor).filter(models.Proveedor.nombre == update_data["nombre"]).first()
         if existing:
              raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Ya existe otro proveedor con el nombre '{update_data['nombre']}'.")

    updated_proveedor = crud.crud_proveedor.update_proveedor(db=db, db_obj=proveedor, obj_in=proveedor_in)
    return updated_proveedor

@router.delete("/{proveedor_id}", response_model=schemas.Proveedor)
def delete_proveedor(
    *,
    db: Session = Depends(deps.get_db),
    proveedor_id: int,
    current_user: "Users" = Depends(deps.require_admin), # Ejemplo
) -> Any:
    """Elimina un proveedor."""
    proveedor = crud.crud_proveedor.get_proveedor(db, proveedor_id=proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    # ON DELETE SET NULL debería manejar los lotes asociados
    deleted_proveedor = crud.crud_proveedor.delete_proveedor(db=db, proveedor_id=proveedor_id)
    return deleted_proveedor