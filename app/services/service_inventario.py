# app/services/service_inventario.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from app import models, schemas, crud
from decimal import Decimal
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Inventario


logger = logging.getLogger(__name__)

def update_inventario_with_adjustment(
    db: Session,
    inventario_id: int,
    obj_in: schemas.InventarioUpdate,
    current_user_id: int | None = None
) -> "Inventario":
    """
    Actualiza un registro de inventario y crea un movimiento de ajuste si la cantidad cambia.
    """
    db_inventario = crud.crud_inventario.get_inventario(db, inventario_id)
    if not db_inventario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de inventario no encontrado.")

    cantidad_anterior = db_inventario.cantidad
    update_data = obj_in.model_dump(exclude_unset=True)
    cantidad_nueva = update_data.get('cantidad', cantidad_anterior) # Obtener nueva cantidad si se proporciona

    try:
        # Actualizar el inventario usando la función CRUD simple
        updated_inventario = crud.crud_inventario.update_inventario_simple(
            db=db, db_obj=db_inventario, obj_in=update_data
        )

        # Calcular diferencia y crear movimiento si es necesario
        diferencia = cantidad_nueva - cantidad_anterior
        if diferencia != 0:
            tipo_movimiento = 'entrada' if diferencia > 0 else 'salida'
            cantidad_movimiento = Decimal(abs(diferencia))
            motivo = f"Ajuste de inventario ID: {updated_inventario.id}"

            mov_create = schemas.MovimientoCreate(
                tipo=tipo_movimiento,
                presentacion_id=updated_inventario.presentacion_id,
                lote_id=updated_inventario.lote_id, # Usar el lote actual del inventario
                cantidad=cantidad_movimiento,
                motivo=motivo
            )
            # Crear movimiento sin commit individual
            mov_obj = crud.crud_movimiento.create_movimiento(db, mov_create, usuario_id=current_user_id)
            db.add(mov_obj) # Añadir movimiento a la sesión

            db.commit() # Commit de actualización de inventario y creación de movimiento
            db.refresh(updated_inventario)
            db.refresh(mov_obj)
            logger.info(f"Inventario ID {updated_inventario.id} actualizado. Movimiento de ajuste ID {mov_obj.id} creado (Cantidad: {diferencia}).")
        else:
            db.commit() # Commit solo la actualización de inventario si no hubo cambio de cantidad
            db.refresh(updated_inventario)
            logger.info(f"Inventario ID {updated_inventario.id} actualizado (sin cambio de cantidad).")

        return updated_inventario

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error SQLAlchemy al actualizar inventario ID {inventario_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al actualizar el inventario.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado al actualizar inventario ID {inventario_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error inesperado al procesar la actualización.")


def delete_inventario_with_adjustment(
    db: Session,
    inventario_id: int,
    current_user_id: int | None = None
) -> "Inventario":
    """
    Elimina un registro de inventario y crea un movimiento de ajuste si la cantidad era > 0.
    """
    db_inventario = crud.crud_inventario.get_inventario(db, inventario_id)
    if not db_inventario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de inventario no encontrado.")

    cantidad_existente = db_inventario.cantidad

    try:
        # Crear movimiento de ajuste de salida si había stock
        if cantidad_existente > 0:
            mov_create = schemas.MovimientoCreate(
                tipo='salida',
                presentacion_id=db_inventario.presentacion_id,
                lote_id=db_inventario.lote_id,
                cantidad=Decimal(cantidad_existente),
                motivo=f"Eliminación de registro Inventario ID: {db_inventario.id}"
            )
            mov_obj = crud.crud_movimiento.create_movimiento(db, mov_create, usuario_id=current_user_id)
            db.add(mov_obj)

        # Eliminar el registro de inventario
        deleted_inventario = crud.crud_inventario.delete_inventario_simple(db, inventario_id=inventario_id)

        db.commit() # Commit de eliminación y posible movimiento
        if 'mov_obj' in locals():
             db.refresh(mov_obj)
             logger.info(f"Inventario ID {inventario_id} eliminado. Movimiento de ajuste ID {mov_obj.id} creado.")
        else:
             logger.info(f"Inventario ID {inventario_id} eliminado (cantidad era 0).")

        return deleted_inventario # Devuelve el objeto antes de eliminarlo de la sesión

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error SQLAlchemy al eliminar inventario ID {inventario_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al eliminar el inventario.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado al eliminar inventario ID {inventario_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error inesperado al procesar la eliminación.")
