# app/services/service_pago.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from app import models, schemas, crud
import logging
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Pago
    from app.models.models import Venta

logger = logging.getLogger(__name__)

def _actualizar_estado_venta(db: Session, venta: "Venta", monto_pago_actual: Decimal = Decimal(0), pago_eliminado_id: int | None = None):
    """Calcula y actualiza el estado de pago de una venta."""
    if not venta:
        return
    total_pagado = sum(p.monto for p in venta.pagos if p.id != pago_eliminado_id) + monto_pago_actual
    saldo = venta.total - total_pagado

    nuevo_estado = 'pendiente'
    if abs(saldo) <= 0.001: # Usar tolerancia
        nuevo_estado = 'pagado'
    elif total_pagado > 0:
        nuevo_estado = 'parcial'

    if venta.estado_pago != nuevo_estado:
        venta.estado_pago = nuevo_estado
        # No se necesita db.add() si el objeto venta ya está en la sesión

def create_pago_and_update_venta(db: Session, pago_in: schemas.PagoCreate, usuario_id: int | None = None) -> "Pago":
    """Crea un pago y actualiza el estado de la venta asociada."""
    venta = crud.crud_venta.get_venta(db, pago_in.venta_id)
    if not venta:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Venta ID {pago_in.venta_id} no encontrada.")

    try:
        # Crear el pago usando la función CRUD (que no hace commit)
        db_pago = crud.crud_pago.create_pago_simple(db, pago_in=pago_in, usuario_id=usuario_id)
        db.add(db_pago) # Añadir a la sesión actual

        # Actualizar estado de la venta
        _actualizar_estado_venta(db, venta, monto_pago_actual=db_pago.monto)

        db.commit() # Commit de pago y actualización de estado de venta
        db.refresh(db_pago)
        db.refresh(venta) # Asegurar que el estado actualizado se cargue
        logger.info(f"Pago ID {db_pago.id} creado para Venta ID {venta.id}")
        return db_pago
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error SQLAlchemy al crear pago para Venta ID {pago_in.venta_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al guardar el pago.")

def delete_pago_and_update_venta(db: Session, pago_id: int) -> "Pago":
    """Elimina un pago y recalcula el estado de la venta asociada."""
    pago = crud.crud_pago.get_pago(db, pago_id)
    if not pago:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Pago ID {pago_id} no encontrado.")

    venta = pago.venta # Acceder a la venta antes de eliminar

    try:
        db.delete(pago)
        _actualizar_estado_venta(db, venta, pago_eliminado_id=pago_id)
        db.commit()
        if venta:
            db.refresh(venta)
        logger.info(f"Pago ID {pago_id} eliminado para Venta ID {venta.id if venta else 'N/A'}")
        return pago # Devolver objeto eliminado
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error SQLAlchemy al eliminar pago ID {pago_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al eliminar el pago.")
