# app/api/v1/endpoints/user.py
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

@router.get("/", response_model=List[schemas.User])

def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=200),
    current_user: "Users" = Depends(deps.require_admin), # Solo admin ve todos los usuarios
) -> Any:
    """Recupera lista de usuarios (solo admin)."""
    users = crud.crud_user.get_users(db, skip=skip, limit=limit)
    return users

# La creación de usuario ya está en auth.py (/register)

@router.get("/{user_id}", response_model=schemas.User)
def read_user_by_id(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user: "Users" = Depends(deps.require_admin), # Solo admin ve otros usuarios por ID
) -> Any:
    """Obtiene un usuario por ID (solo admin)."""
    user = crud.crud_user.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@router.put("/{user_id}", response_model=schemas.User)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: schemas.UserUpdate,
    current_user: "Users" = Depends(deps.require_admin), # Solo admin actualiza otros usuarios
) -> Any:
    """Actualiza un usuario (solo admin)."""
    user = crud.crud_user.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    update_data = user_in.model_dump(exclude_unset=True)
    # Verificar username si se cambia
    if "username" in update_data and update_data["username"] != user.username:
        existing = crud.crud_user.get_user_by_username(db, username=update_data["username"])
        if existing:
             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El nombre de usuario ya existe.")
    # Verificar almacen si se cambia
    if "almacen_id" in update_data and update_data["almacen_id"]:
         almacen = crud.crud_almacen.get_almacen(db, update_data["almacen_id"])
         if not almacen:
              raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Almacén ID {update_data['almacen_id']} no encontrado.")


    updated_user = crud.crud_user.update_user(db=db, db_obj=user, obj_in=user_in)
    return updated_user

# PUT para que el usuario actualice su PROPIA información (ej: contraseña)
@router.put("/me", response_model=schemas.User)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserUpdate, # Usar el mismo esquema, pero filtrar campos
    current_user: "Users" = Depends(deps.get_current_active_user),
) -> Any:
    """Update own user."""
    # Filtrar campos que el usuario NO puede cambiarse a sí mismo (ej: rol, username?)
    allowed_data = {}
    if user_in.password is not None:
        allowed_data["password"] = user_in.password
    # Añadir otros campos si se permiten (ej: ¿email?, ¿teléfono?)
    # if user_in.email is not None: allowed_data["email"] = user_in.email

    if not allowed_data:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No hay datos actualizables proporcionados.")

    updated_user = crud.crud_user.update_user(db=db, db_obj=current_user, obj_in=allowed_data)
    return updated_user


@router.delete("/{user_id}", response_model=schemas.User)
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: "Users" = Depends(deps.require_admin), # Solo admin elimina
) -> Any:
    """Elimina un usuario (solo admin)."""
    user = crud.crud_user.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if user.id == current_user.id:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Los administradores no pueden eliminarse a sí mismos.")
    deleted_user = crud.crud_user.delete_user(db=db, user_id=user_id)
    return deleted_user