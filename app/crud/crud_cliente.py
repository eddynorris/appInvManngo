# app/crud/crud_cliente.py
from sqlalchemy.orm import Session
from app import models, schemas # Nota: app/models y app/schemas
from fastapi.encoders import jsonable_encoder # Útil para convertir Pydantic a dict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Cliente


def get_cliente(db: Session, cliente_id: int):
    return db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()

def get_clientes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Cliente).offset(skip).limit(limit).all()

def create_cliente(db: Session, cliente: schemas.ClienteCreate):
    db_cliente = models.Cliente(**cliente.model_dump()) # Pydantic v2
    # db_cliente = models.Cliente(**cliente.dict()) # Pydantic v1
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente

def update_cliente(db: Session, db_obj: "Cliente", obj_in: schemas.ClienteUpdate | dict):
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True) # Pydantic v2
        # update_data = obj_in.dict(exclude_unset=True) # Pydantic v1

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_cliente(db: Session, cliente_id: int):
    db_obj = db.query(models.Cliente).get(cliente_id)
    if db_obj:
        db.delete(db_obj)
        db.commit()
    return db_obj

# --- Funciones adicionales específicas si las necesitas ---
# def get_cliente_by_nombre(db: Session, nombre: str): ...