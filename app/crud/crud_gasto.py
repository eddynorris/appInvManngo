# app/crud/crud_gasto.py
from sqlalchemy.orm import Session
from app import models, schemas
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Gasto


def get_gasto(db: Session, gasto_id: int):
    return db.query(models.Gasto).filter(models.Gasto.id == gasto_id).first()

def get_gastos(db: Session, skip: int = 0, limit: int = 100, **filters):
    query = db.query(models.Gasto)
    if filters.get("almacen_id"):
        query = query.filter(models.Gasto.almacen_id == filters["almacen_id"])
    if filters.get("categoria"):
        query = query.filter(models.Gasto.categoria == filters["categoria"])
    if filters.get("usuario_id"):
        query = query.filter(models.Gasto.usuario_id == filters["usuario_id"])
    # Añadir filtro por fecha si es necesario
    return query.order_by(models.Gasto.fecha.desc()).offset(skip).limit(limit).all()

def create_gasto(db: Session, gasto: schemas.GastoCreate, usuario_id: int | None = None):
    gasto_data = gasto.model_dump()
    if usuario_id:
        gasto_data['usuario_id'] = usuario_id
    db_gasto = models.Gasto(**gasto_data)
    db.add(db_gasto)
    db.commit()
    db.refresh(db_gasto)
    return db_gasto

def update_gasto(db: Session, db_obj: "Gasto", obj_in: schemas.GastoUpdate | dict):
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

def delete_gasto(db: Session, gasto_id: int):
    db_obj = db.query(models.Gasto).get(gasto_id)
    if db_obj:
        db.delete(db_obj)
        db.commit()
    return db_obj