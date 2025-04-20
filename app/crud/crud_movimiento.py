# app/crud/crud_movimiento.py
from sqlalchemy.orm import Session
from app import models, schemas

def get_movimiento(db: Session, movimiento_id: int):
    return db.query(models.Movimiento).filter(models.Movimiento.id == movimiento_id).first()

def get_movimientos(db: Session, skip: int = 0, limit: int = 100, **filters):
    query = db.query(models.Movimiento)
    if filters.get("presentacion_id"):
        query = query.filter(models.Movimiento.presentacion_id == filters["presentacion_id"])
    if filters.get("lote_id"):
        query = query.filter(models.Movimiento.lote_id == filters["lote_id"])
    if filters.get("tipo"):
        query = query.filter(models.Movimiento.tipo == filters["tipo"])
    # Añadir más filtros...
    return query.order_by(models.Movimiento.fecha.desc()).offset(skip).limit(limit).all()

def create_movimiento(db: Session, movimiento: schemas.MovimientoCreate, usuario_id: int | None = None):
    mov_data = movimiento.model_dump()
    if usuario_id:
        mov_data['usuario_id'] = usuario_id
    db_movimiento = models.Movimiento(**mov_data)
    db.add(db_movimiento)
    # No hacemos commit aquí si se llama desde otra función (ej: create_venta)
    # db.commit()
    # db.refresh(db_movimiento)
    return db_movimiento # Devolver el objeto sin commit