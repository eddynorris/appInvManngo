# app/crud/crud_pago.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app import models, schemas, crud # Mantener crud para posible uso futuro
from decimal import Decimal
import logging # Añadir logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Pago

logger = logging.getLogger(__name__)

def get_pago(db: Session, pago_id: int):
    return db.query(models.Pago).filter(models.Pago.id == pago_id).first()

def get_pagos(db: Session, skip: int = 0, limit: int = 100, venta_id: int | None = None):
    query = db.query(models.Pago)
    if venta_id:
        query = query.filter(models.Pago.venta_id == venta_id)
    return query.order_by(models.Pago.fecha.desc()).offset(skip).limit(limit).all()

def create_pago_simple(db: Session, pago_in: schemas.PagoCreate, usuario_id: int | None = None) -> "Pago":
    """Crea un registro de pago sin actualizar venta ni hacer commit."""
    pago_data = pago_in.model_dump()
    if usuario_id:
        pago_data['usuario_id'] = usuario_id
    db_pago = models.Pago(**pago_data)
    # db.add(db_pago) # El servicio lo añadirá
    return db_pago

def update_pago_simple(db: Session, db_obj: "Pago", obj_in: schemas.PagoUpdate | dict):
    """Actualiza campos simples de un pago (referencia, url_comprobante)."""
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True)

    # Evitar actualizar campos críticos
    allowed_updates = ['referencia', 'url_comprobante']
    for field, value in update_data.items():
        if field in allowed_updates:
            setattr(db_obj, field, value)

    db.add(db_obj)
    try:
        db.commit() # Permitir commit para updates simples
        db.refresh(db_obj)
        return db_obj
    except Exception as e:
        db.rollback()
        logger.error(f"Error en update_pago_simple: {e}", exc_info=True)
        raise

def delete_pago_simple(db: Session, pago_id: int):
    """Elimina un pago sin actualizar la venta."""
    db_obj = db.query(models.Pago).get(pago_id)
    if db_obj:
        db.delete(db_obj)
        # No hacer commit, lo manejará el servicio
    return db_obj