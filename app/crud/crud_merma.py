# app/crud/crud_merma.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app import models, schemas
from decimal import Decimal
from app.services import service_merma
import logging # Añadir logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Merma


logger = logging.getLogger(__name__)

def get_merma(db: Session, merma_id: int):
    return db.query(models.Merma).filter(models.Merma.id == merma_id).first()

def get_mermas(db: Session, skip: int = 0, limit: int = 100, lote_id: int | None = None):
    query = db.query(models.Merma)
    if lote_id:
        query = query.filter(models.Merma.lote_id == lote_id)
    return query.offset(skip).limit(limit).all()

def create_merma_simple(db: Session, merma: schemas.MermaCreate, usuario_id: int | None = None) -> "Merma":
    """Crea un registro de merma sin actualizar el lote ni hacer commit."""
    merma_data = merma.model_dump()
    if usuario_id:
        merma_data['usuario_id'] = usuario_id
    db_merma = models.Merma(**merma_data)
    # db.add(db_merma) # El servicio lo añadirá a la sesión
    return db_merma

def update_merma_simple(db: Session, db_obj: "Merma", obj_in: schemas.MermaUpdate | dict):
    """Actualiza campos simples de una merma (ej: convertido_a_briquetas)."""
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    try:
        db.commit() # Permitir commit para updates simples
        db.refresh(db_obj)
        return db_obj
    except Exception as e:
        db.rollback()
        logger.error(f"Error en update_merma_simple: {e}", exc_info=True)
        raise

def delete_merma_simple(db: Session, merma_id: int):
    """Elimina una merma sin restaurar el lote."""
    db_obj = db.query(models.Merma).get(merma_id)
    if db_obj:
        db.delete(db_obj)
        # No hacer commit, lo manejará el servicio si necesita restaurar lote
    return db_obj