# app/schemas/schema_user.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from .schema_almacen import Almacen # Importar el esquema Pydantic de Almacen

# Esquema base con campos comunes (sin contraseña)
class UserBase(BaseModel):
    username: str = Field(..., max_length=80)
    rol: str = Field(default='usuario', pattern="^(admin|gerente|usuario)$") # Validar roles
    almacen_id: Optional[int] = None

# Esquema para crear un usuario (incluye contraseña)
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

# Esquema para actualizar (contraseña opcional)
class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, max_length=80)
    password: Optional[str] = Field(None, min_length=6)
    rol: Optional[str] = Field(None, pattern="^(admin|gerente|usuario)$")
    almacen_id: Optional[int] = None

# Esquema para leer/retornar (NUNCA incluir contraseña)
class User(UserBase):
    id: int
    almacen: Optional[Almacen] = None # Anidar info básica del almacén

    class Config:
        from_attributes = True

# Esquema para el login
class UserLogin(BaseModel):
    username: str
    password: str