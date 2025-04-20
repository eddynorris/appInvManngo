# app/crud/crud_proveedor.py
from sqlalchemy.orm import Session
from app import models, schemas
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Proveedor

def get_proveedor(db: Session, proveedor_id: int):
    return db.query(models.Proveedor).filter(models.Proveedor.id == proveedor_id).first()

def get_proveedores(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Proveedor).offset(skip).limit(limit).all()

def create_proveedor(db: Session, proveedor: schemas.ProveedorCreate):
    db_proveedor = models.Proveedor(**proveedor.model_dump())
    db.add(db_proveedor)
    db.commit()
    db.refresh(db_proveedor)
    return db_proveedor

def update_proveedor(db: Session, db_obj: "Proveedor", obj_in: schemas.ProveedorUpdate | dict):
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

def delete_proveedor(db: Session, proveedor_id: int):
    db_obj = db.query(models.Proveedor).get(proveedor_id)
    if db_obj:
        # Considerar qué pasa con los lotes asociados (ON DELETE SET NULL)
        db.delete(db_obj)
        db.commit()
    return db_obj