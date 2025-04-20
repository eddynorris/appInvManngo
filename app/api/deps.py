# app/api/deps.py
from typing import Generator, Optional, TYPE_CHECKING
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from pydantic import ValidationError

from app.db.session import SessionLocal
from app.core import security
from app.core.config import settings
from app import models, schemas, crud

# Definir el tipo dentro de TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.models import Users

# Define el esquema de autenticación
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token") # Ajusta la URL a tu endpoint de login

def get_db() -> Generator:
    """Inyecta una sesión de base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> "Users":
    """Obtiene el usuario actual a partir del token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = security.decode_access_token(token)
    if payload is None:
        raise credentials_exception
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    user = crud.user.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(
    current_user: "Users" = Depends(get_current_user),
) -> "Users":
    """Verifica si el usuario actual está activo (puedes añadir lógica de 'activo' en tu modelo User)."""
    # if not current_user.is_active: # Si tuvieras un campo is_active
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Puedes crear dependencias para roles específicos
def get_current_admin_user(
    current_user: "Users" = Depends(get_current_active_user),
) -> "Users":
    if current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The user doesn't have enough privileges"
        )
    return current_user

def require_admin(current_user: "Users" = Depends(get_current_active_user)) -> "Users":
    """Dependencia que exige rol 'admin'."""
    if not current_user or current_user.rol != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acción restringida a administradores."
        )
    return current_user

def require_rol(*roles: str):
    """Dependencia genérica para requerir uno o más roles."""
    def role_checker(current_user: "Users" = Depends(get_current_active_user)) -> "Users":
        if not current_user or current_user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requiere rol: {', '.join(roles)}."
            )
        return current_user
    return role_checker

def get_verified_almacen(
    almacen_id_param: int, # ID del almacén del recurso que se quiere acceder/modificar
    current_user: "Users" = Depends(get_current_active_user)
) -> int:
    """
    Verifica si el usuario puede acceder/modificar el almacén especificado.
    Devuelve el almacen_id si es válido, o lanza HTTPException 403.
    """
    if current_user.rol == 'admin':
        # Admin puede acceder a cualquier almacén válido
        # (Podrías añadir una verificación de que almacen_id_param existe en la BD si es necesario)
        return almacen_id_param
    elif current_user.almacen_id == almacen_id_param:
        # Usuario normal solo accede a su propio almacén
        return almacen_id_param
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permiso para operar sobre este almacén."
        )
