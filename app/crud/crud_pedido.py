# app/crud/crud_pedido.py (Simplificado)
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status # Asegurar import
from app import models, schemas, crud
from decimal import Decimal
import logging # Usar logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Pedido


logger = logging.getLogger(__name__)

def get_pedido(db: Session, pedido_id: int):
    # Considerar options(joinedload(...)) para cargar relaciones
    return db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()

def get_pedidos(db: Session, skip: int = 0, limit: int = 100, **filters):
    query = db.query(models.Pedido)
    # Aplicar filtros (cliente_id, almacen_id, vendedor_id, estado, fechas, etc.)
    if filters.get("cliente_id"):
        query = query.filter(models.Pedido.cliente_id == filters["cliente_id"])
    if filters.get("almacen_id"):
         query = query.filter(models.Pedido.almacen_id == filters["almacen_id"])
    if filters.get("vendedor_id"):
         query = query.filter(models.Pedido.vendedor_id == filters["vendedor_id"])
    if filters.get("estado"):
         query = query.filter(models.Pedido.estado == filters["estado"])
    # Añadir filtro por fechas si es necesario
    return query.order_by(models.Pedido.fecha_creacion.desc()).offset(skip).limit(limit).all()

def create_pedido_simple(db: Session, pedido_in: schemas.PedidoCreate, vendedor_id: int) -> "Pedido":
    """Crea un registro de pedido y sus detalles, sin commit."""
    pedido_detalles_in = pedido_in.detalles
    pedido_base_data = pedido_in.model_dump(exclude={'detalles'})

    # Validaciones simples (existencia) se pueden hacer aquí o en el endpoint/servicio
    if not crud.crud_cliente.get_cliente(db, pedido_in.cliente_id):
         raise ValueError(f"Cliente ID {pedido_in.cliente_id} no encontrado.")
    if not crud.crud_almacen.get_almacen(db, pedido_in.almacen_id):
         raise ValueError(f"Almacén ID {pedido_in.almacen_id} no encontrado.")

    detalles_db = []
    for detalle_in in pedido_detalles_in:
        if not crud.crud_presentacion.get_presentacion(db, detalle_in.presentacion_id):
             raise ValueError(f"Presentación ID {detalle_in.presentacion_id} no encontrada.")
        detalles_db.append(models.PedidoDetalle(**detalle_in.model_dump()))

    db_pedido = models.Pedido(
        **pedido_base_data,
        vendedor_id=vendedor_id,
        detalles=detalles_db
    )
    db.add(db_pedido)
    # NO COMMIT HERE - El servicio o endpoint se encargará
    return db_pedido

def update_pedido_simple(db: Session, db_obj: "Pedido", obj_in: schemas.PedidoUpdate | dict):
    """Actualiza campos simples de un pedido. Hace commit."""
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True)

    # Evitar actualizar campos no permitidos directamente
    disallowed_updates = ['cliente_id', 'almacen_id', 'vendedor_id', 'detalles']
    for field in disallowed_updates:
        if field in update_data:
            del update_data[field]

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    try:
        db.commit()
        db.refresh(db_obj)
        return db_obj
    except Exception as e:
        db.rollback()
        logger.error(f"Error en update_pedido_simple para Pedido ID {db_obj.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al actualizar el pedido.")


def delete_pedido_simple(db: Session, pedido_id: int):
    """Elimina un pedido. Hace commit."""
    db_obj = db.query(models.Pedido).get(pedido_id)
    if db_obj:
        try:
            db.delete(db_obj) # ON DELETE CASCADE elimina detalles
            db.commit()
        except Exception as e:
             db.rollback()
             logger.error(f"Error en delete_pedido_simple para Pedido ID {pedido_id}: {e}", exc_info=True)
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al eliminar el pedido.")

    return db_obj # Devuelve el objeto (o None si no se encontró)