# app/crud/crud_producto.py
from sqlalchemy.orm import Session
from app import models, schemas
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Producto


def get_producto(db: Session, producto_id: int):
    return db.query(models.Producto).filter(models.Producto.id == producto_id).first()

def get_productos(db: Session, skip: int = 0, limit: int = 100, activo: bool | None = None):
    query = db.query(models.Producto)
    if activo is not None:
        query = query.filter(models.Producto.activo == activo)
    return query.offset(skip).limit(limit).all()

def create_producto(db: Session, producto: schemas.ProductoCreate):
    db_producto = models.Producto(**producto.model_dump())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

def update_producto(db: Session, db_obj: "Producto", obj_in: schemas.ProductoUpdate | dict):
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_producto(db: Session, producto_id: int):
    db_obj = db.query(models.Producto).get(producto_id)
    if db_obj:
        # ON DELETE CASCADE manejará presentaciones, lotes, etc.
        db.delete(db_obj)
        db.commit()
    return db_obj