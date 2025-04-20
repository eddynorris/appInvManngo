# app/api/v1/endpoints/producto.py
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

@router.get("/", response_model=List[schemas.Producto])
def read_productos(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=200),
    activo: bool | None = Query(default=None, description="Filtrar por estado activo/inactivo"),
    current_user: "Users" = Depends(deps.get_current_active_user), # Acceso público?
) -> Any:
    """Recupera lista de productos."""
    productos = crud.crud_producto.get_productos(db, skip=skip, limit=limit, activo=activo)
    return productos

@router.post("/", response_model=schemas.Producto, status_code=status.HTTP_201_CREATED)
def create_producto(
    *,
    db: Session = Depends(deps.get_db),
    producto_in: schemas.ProductoCreate,
    current_user: "Users" = Depends(deps.require_rol('admin', 'gerente')), # Ejemplo
) -> Any:
    """Crea un nuevo producto."""
    # Podría verificar si el nombre ya existe
    existing_producto = db.query(models.Producto).filter(models.Producto.nombre == producto_in.nombre).first()
    if existing_producto:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Ya existe un producto con el nombre '{producto_in.nombre}'.")
    producto = crud.crud_producto.create_producto(db=db, producto=producto_in)
    return producto

@router.get("/{producto_id}", response_model=schemas.Producto)
def read_producto_by_id(
    producto_id: int,
    db: Session = Depends(deps.get_db),
    current_user: "Users" = Depends(deps.get_current_active_user), # Acceso público?
) -> Any:
    """Obtiene un producto por ID."""
    producto = crud.crud_producto.get_producto(db, producto_id=producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

@router.put("/{producto_id}", response_model=schemas.Producto)
def update_producto(
    *,
    db: Session = Depends(deps.get_db),
    producto_id: int,
    producto_in: schemas.ProductoUpdate,
    current_user: "Users" = Depends(deps.require_rol('admin', 'gerente')), # Ejemplo
) -> Any:
    """Actualiza un producto."""
    producto = crud.crud_producto.get_producto(db, producto_id=producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Verificar si el nuevo nombre ya existe en otro producto
    update_data = producto_in.model_dump(exclude_unset=True)
    if "nombre" in update_data and update_data["nombre"] != producto.nombre:
         existing = db.query(models.Producto).filter(models.Producto.nombre == update_data["nombre"]).first()
         if existing:
              raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Ya existe otro producto con el nombre '{update_data['nombre']}'.")

    updated_producto = crud.crud_producto.update_producto(db=db, db_obj=producto, obj_in=producto_in)
    return updated_producto

@router.delete("/{producto_id}", response_model=schemas.Producto)
def delete_producto(
    *,
    db: Session = Depends(deps.get_db),
    producto_id: int,
    current_user: "Users" = Depends(deps.require_admin), # Ejemplo: Solo admin elimina
) -> Any:
    """Elimina un producto."""
    producto = crud.crud_producto.get_producto(db, producto_id=producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    # ON DELETE CASCADE debería manejar dependencias (presentaciones, lotes, etc.)
    deleted_producto = crud.crud_producto.delete_producto(db=db, producto_id=producto_id)
    return deleted_producto