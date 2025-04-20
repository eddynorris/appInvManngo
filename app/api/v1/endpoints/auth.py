# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any
from datetime import timedelta
from app import crud, schemas, models
from app.api import deps
from app.core import security
from app.core.config import settings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Users


router = APIRouter()
@router.post("/token", response_model=schemas.Token)
def login_for_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = crud.crud_user.authenticate_user(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Aquí podrías añadir lógica para verificar si el usuario está activo
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username, "rol": user.rol, "almacen_id": user.almacen_id}, # Añadir claims necesarios
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}
@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register_new_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
    # current_user: models.Users = Depends(deps.require_admin) # ¿Solo admin registra? O permitir autoregistro?
) -> Any:
    """
    Crea un nuevo usuario.
    (Ajustar permisos según necesidad - ¿público o solo admin?)
    """
    user = crud.crud_user.get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya existe.",
        )
    # Verificar si almacen_id existe (si se proporciona)
    if user_in.almacen_id:
         almacen = crud.crud_almacen.get_almacen(db, user_in.almacen_id)
         if not almacen:
              raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Almacén ID {user_in.almacen_id} no encontrado.")
    new_user = crud.crud_user.create_user(db=db, user=user_in)
    return new_user
# Podrías añadir un endpoint /me para obtener datos del usuario actual
@router.get("/me", response_model=schemas.User)
def read_users_me(
    current_user: "Users" = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user