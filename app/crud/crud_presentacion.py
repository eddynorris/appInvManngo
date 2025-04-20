# app/crud/crud_presentacion.py
from sqlalchemy.orm import Session
from app import models, schemas
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import PresentacionProducto  

def get_presentacion(db: Session, presentacion_id: int):
    return db.query(models.PresentacionProducto).filter(models.PresentacionProducto.id == presentacion_id).first()

def get_presentaciones(db: Session, skip: int = 0, limit: int = 100, producto_id: int | None = None, activo: bool | None = None):
    query = db.query(models.PresentacionProducto)
    if producto_id is not None:
        query = query.filter(models.PresentacionProducto.producto_id == producto_id)
    if activo is not None:
        query = query.filter(models.PresentacionProducto.activo == activo)
    return query.offset(skip).limit(limit).all()

def create_presentacion(db: Session, presentacion: schemas.PresentacionCreate):
    db_presentacion = models.PresentacionProducto(**presentacion.model_dump())
    db.add(db_presentacion)
    db.commit()
    db.refresh(db_presentacion)
    return db_presentacion

def update_presentacion(db: Session, db_obj: "PresentacionProducto", obj_in: schemas.PresentacionUpdate | dict):
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

def delete_presentacion(db: Session, presentacion_id: int):
    db_obj = db.query(models.PresentacionProducto).get(presentacion_id)
    if db_obj:
        # ON DELETE CASCADE manejará inventario, detalles de venta/pedido
        db.delete(db_obj)
        db.commit()
    return db_obj