# app/crud/crud_lote.py
from sqlalchemy.orm import Session
from app import models, schemas
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Lote

def get_lote(db: Session, lote_id: int):
    return db.query(models.Lote).filter(models.Lote.id == lote_id).first()

def get_lotes(db: Session, skip: int = 0, limit: int = 100, producto_id: int | None = None, proveedor_id: int | None = None):
    query = db.query(models.Lote)
    if producto_id is not None:
        query = query.filter(models.Lote.producto_id == producto_id)
    if proveedor_id is not None:
        query = query.filter(models.Lote.proveedor_id == proveedor_id)
    return query.order_by(models.Lote.fecha_ingreso.desc()).offset(skip).limit(limit).all()

def create_lote(db: Session, lote: schemas.LoteCreate):
    lote_data = lote.model_dump()
    # Si no se proporciona cantidad disponible, inicializarla (ej: con peso húmedo)
    if lote_data.get('cantidad_disponible_kg') is None:
        lote_data['cantidad_disponible_kg'] = lote_data.get('peso_humedo_kg')

    db_lote = models.Lote(**lote_data)
    db.add(db_lote)
    db.commit()
    db.refresh(db_lote)
    return db_lote

def update_lote(db: Session, db_obj: "Lote", obj_in: schemas.LoteUpdate | dict):
    # Simple update, no recalcula lógicas complejas aquí
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

def delete_lote(db: Session, lote_id: int):
    db_obj = db.query(models.Lote).get(lote_id)
    if db_obj:
        # Considerar qué pasa con inventario, mermas, movimientos asociados (ON DELETE SET NULL)
        db.delete(db_obj)
        db.commit()
    return db_obj

def update_cantidad_disponible_lote(db: Session, lote_id: int, cantidad_a_restar: Decimal):
    """Función auxiliar para ajustar cantidad disponible (llamada desde servicios)."""
    lote = db.query(models.Lote).filter(models.Lote.id == lote_id).with_for_update().first()
    if not lote:
        raise ValueError(f"Lote con ID {lote_id} no encontrado para actualizar cantidad.")
    if lote.cantidad_disponible_kg is None or lote.cantidad_disponible_kg < cantidad_a_restar:
         raise ValueError(f"Cantidad insuficiente en lote {lote.id}. Disponible: {lote.cantidad_disponible_kg}")
    lote.cantidad_disponible_kg -= cantidad_a_restar
    db.add(lote)
    # No hacer commit aquí, se hará en la transacción del servicio
    return lote