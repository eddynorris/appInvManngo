# app/crud/crud_inventario.py
from sqlalchemy.orm import Session
from app import models, schemas
import logging # Añadir logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Inventario



logger = logging.getLogger(__name__)

def get_inventario(db: Session, inventario_id: int):
    return db.query(models.Inventario).filter(models.Inventario.id == inventario_id).first()

def get_inventario_by_presentacion_almacen(db: Session, presentacion_id: int, almacen_id: int):
     return db.query(models.Inventario).filter(
         models.Inventario.presentacion_id == presentacion_id,
         models.Inventario.almacen_id == almacen_id
     ).first()

def get_inventarios(db: Session, skip: int = 0, limit: int = 100, almacen_id: int | None = None):
    query = db.query(models.Inventario)
    if almacen_id:
        query = query.filter(models.Inventario.almacen_id == almacen_id)
    # Añadir más filtros si es necesario (por presentación, lote, etc.)
    return query.offset(skip).limit(limit).all()

def create_inventario_simple(db: Session, inventario: schemas.InventarioCreate):
    """Crea un registro de inventario sin lógica de movimientos."""
    # Nota: Podría ser útil que el servicio llame a esta función
    # y luego cree un movimiento de entrada inicial.
    db_inventario = models.Inventario(**inventario.model_dump())
    db.add(db_inventario)
    # Commit aquí o manejarlo en el servicio? Por consistencia con otros CRUD simples, lo dejamos.
    try:
        db.commit()
        db.refresh(db_inventario)
        return db_inventario
    except Exception as e:
        db.rollback()
        logger.error(f"Error en create_inventario_simple: {e}", exc_info=True)
        raise

def update_inventario_simple(db: Session, db_obj: "Inventario", obj_in: schemas.InventarioUpdate | dict):
    """Actualiza campos simples de un registro de inventario. No maneja movimientos."""
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj) # Añadir a la sesión para marcar como 'dirty'
    # No hacer commit aquí, lo manejará el servicio que lo llame
    return db_obj

def delete_inventario_simple(db: Session, inventario_id: int):
    """Elimina un registro de inventario sin crear movimientos."""
    db_obj = db.query(models.Inventario).get(inventario_id)
    if db_obj:
        db.delete(db_obj)
        # No hacer commit aquí, lo manejará el servicio
    return db_obj # Devuelve el objeto para referencia (antes de commit/expunge)