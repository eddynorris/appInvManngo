# app/crud/crud_user.py
from sqlalchemy.orm import Session
from app.models.models import Users
from app import schemas
from app.core import security
from typing import Any, Dict, Optional, Union, List, TYPE_CHECKING

if TYPE_CHECKING:
    pass

def get_user(db: Session, user_id: int) -> Optional[Users]:
    return db.query(Users).filter(Users.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[Users]:
    return db.query(Users).filter(Users.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[Users]:
    return db.query(Users).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate) -> Users:
    hashed_password = security.get_password_hash(user.password)
    db_user = Users(
        username=user.username,
        password=hashed_password,
        rol=user.rol,
        almacen_id=user.almacen_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, db_obj: "Users", obj_in: schemas.UserUpdate | dict) -> "Users":
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True)

    if "password" in update_data and update_data["password"]:
        hashed_password = security.get_password_hash(update_data["password"])
        setattr(db_obj, 'password', hashed_password)
        del update_data["password"]

    for field, value in update_data.items():
         setattr(db_obj, field, value)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_user(db: Session, user_id: int) -> Optional[Users]:
    db_user = db.query(Users).get(user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

def authenticate_user(db: Session, username: str, password: str) -> Optional["Users"]:
     user = get_user_by_username(db, username=username)
     if not user:
         return None
     if not security.verify_password(password, user.password):
         return None
     return user