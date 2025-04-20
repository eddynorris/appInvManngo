# app/crud/crud_venta.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app import models, schemas # Importar otros cruds si update lo necesita
from decimal import Decimal
from datetime import datetime, timezone
import logging # Añadir logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Venta

logger = logging.getLogger(__name__)

def get_venta(db: Session, venta_id: int):
    # Considerar options(joinedload(...)) para cargar relaciones si siempre se necesitan
    return db.query(models.Venta).filter(models.Venta.id == venta_id).first()

def get_ventas(db: Session, skip: int = 0, limit: int = 100, **filters):
    query = db.query(models.Venta)
    # Aplicar filtros (cliente_id, almacen_id, vendedor_id, fechas, estado_pago, etc.)
    if filters.get("cliente_id"):
        query = query.filter(models.Venta.cliente_id == filters["cliente_id"])
    if filters.get("almacen_id"):
        query = query.filter(models.Venta.almacen_id == filters["almacen_id"])
    if filters.get("vendedor_id"):
        query = query.filter(models.Venta.vendedor_id == filters["vendedor_id"])
    if filters.get("estado_pago"):
        query = query.filter(models.Venta.estado_pago == filters["estado_pago"])
    # Añadir más filtros... Fechas requerirán conversión a datetime
    # Ejemplo filtro fecha:
    # if filters.get("fecha_inicio") and filters.get("fecha_fin"):
    #     try:
    #         fecha_inicio = datetime.fromisoformat(filters["fecha_inicio"])
    #         fecha_fin = datetime.fromisoformat(filters["fecha_fin"])
    #         query = query.filter(models.Venta.fecha.between(fecha_inicio, fecha_fin))
    #     except ValueError:
    #         logger.warning("Formato de fecha inválido para filtro de ventas.")
    #         # Considerar lanzar un error aquí o devolver lista vacía

    return query.order_by(models.Venta.fecha.desc()).offset(skip).limit(limit).all()


def update_venta_simple(db: Session, db_obj: "Venta", obj_in: schemas.VentaUpdate | dict):
    """Actualiza campos simples de una venta. No maneja detalles ni recalcula estados/totales."""
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True)

    # Asegurar que campos críticos no se actualicen directamente aquí
    disallowed_updates = ['cliente_id', 'almacen_id', 'vendedor_id', 'total', 'detalles']
    for field in disallowed_updates:
        if field in update_data:
            del update_data[field] # Ignorar intentos de actualizar campos no permitidos

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    try:
        db.commit() # Permitir commit para updates simples
        db.refresh(db_obj)
        return db_obj
    except Exception as e:
        db.rollback()
        logger.error(f"Error en update_venta_simple para Venta ID {db_obj.id}: {e}", exc_info=True)
        raise

# Las funciones create_venta y delete_venta complejas se eliminan de aquí.
# Ahora están en app/services/service_venta.py