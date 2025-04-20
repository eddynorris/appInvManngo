# app/services/service_merma.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from app import models, schemas, crud
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Merma

logger = logging.getLogger(__name__)

def create_merma_and_update_lote(db: Session, merma: schemas.MermaCreate, current_user_id: int | None = None) -> "Merma":
    """Crea una merma y actualiza la cantidad disponible del lote asociado."""
    try:
        # 1. Actualizar cantidad del lote (usando función CRUD auxiliar)
        lote = crud.crud_lote.update_cantidad_disponible_lote(
            db,
            lote_id=merma.lote_id,
            cantidad_a_restar=merma.cantidad_kg
        )

        # 2. Crear el registro de merma (usando función CRUD simple)
        db_merma = crud.crud_merma.create_merma_simple(
            db,
            merma=merma,
            usuario_id=current_user_id
        )
        db.add(db_merma) # Añadir a la sesión

        db.commit() # Commit de ambas operaciones
        db.refresh(db_merma)
        db.refresh(lote)
        logger.info(f"Merma ID {db_merma.id} creada para Lote ID {lote.id}")
        return db_merma

    except (SQLAlchemyError, ValueError) as e: # Captura errores de BD o validación de cantidad
        db.rollback()
        logger.error(f"Error al crear merma para Lote ID {merma.lote_id}: {e}", exc_info=True)
        # Determinar el código de estado adecuado
        status_code = status.HTTP_409_CONFLICT if isinstance(e, ValueError) else status.HTTP_500_INTERNAL_SERVER_ERROR
        detail = str(e) if isinstance(e, ValueError) else "Error interno al registrar la merma."
        raise HTTPException(status_code=status_code, detail=detail)