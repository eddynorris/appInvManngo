# app/services/service_pedido.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from app import models, schemas, crud, services # Importar otros servicios
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Venta

logger = logging.getLogger(__name__)

def convert_pedido_to_venta(db: Session, pedido_id: int, current_user_id: int) -> "Venta":
    """
    Convierte un Pedido existente en una Venta.
    Verifica stock, crea la venta, actualiza estado del pedido.
    """
    pedido = crud.crud_pedido.get_pedido(db, pedido_id)
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Pedido ID {pedido_id} no encontrado.")
    if pedido.estado != 'confirmado': # Solo convertir pedidos confirmados (o la lógica que definas)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Solo se pueden convertir pedidos en estado 'confirmado'. Estado actual: {pedido.estado}")
    # Crear objeto VentaCreate a partir de los datos del pedido
    detalles_venta_in = []
    for det_pedido in pedido.detalles:
        # Podrías re-validar precio aquí o usar el precio_estimado
        # Usaremos precio_estimado como precio_unitario de venta
        detalles_venta_in.append(schemas.VentaDetalleCreate(
            presentacion_id=det_pedido.presentacion_id,
            cantidad=det_pedido.cantidad,
            precio_unitario=det_pedido.precio_estimado # ¡Importante! Decide si este es el precio final
        ))
    # Asumir tipo_pago por defecto o requerir input adicional? Usaremos 'credito'
    venta_in = schemas.VentaCreate(
        cliente_id=pedido.cliente_id,
        almacen_id=pedido.almacen_id,
        # vendedor_id se asigna desde current_user_id
        tipo_pago='credito', # O determina según lógica de negocio
        estado_pago='pendiente', # Estado inicial de la nueva venta
        # consumo_diario_kg podría venir del cliente o ser opcional
        consumo_diario_kg=pedido.cliente.consumo_diario_kg if pedido.cliente else None,
        detalles=detalles_venta_in
        # El total se calculará en el servicio de venta
    )
    try:
        # Llamar al servicio de venta para crearla (maneja stock, movs, etc.)
        nueva_venta = services.service_venta.create_venta_with_details(
            db=db,
            venta_in=venta_in,
            vendedor_id=current_user_id # El usuario que convierte es el vendedor
        )
        # Actualizar estado del pedido a 'entregado' (o 'facturado')
        pedido.estado = 'entregado' # O el estado apropiado
        db.add(pedido)
        db.commit() # Commit de la creación de venta y actualización de estado pedido
        db.refresh(nueva_venta)
        # db.refresh(pedido) # No necesario si solo cambiamos estado y commiteamos
        logger.info(f"Pedido ID {pedido_id} convertido a Venta ID {nueva_venta.id} por Usuario ID {current_user_id}")
        return nueva_venta
    except HTTPException as http_exc:
        db.rollback() # Asegurar rollback si create_venta_with_details falló con HTTPException
        logger.warning(f"Fallo al convertir Pedido ID {pedido_id} a Venta: {http_exc.detail}")
        raise http_exc # Re-lanzar excepción HTTP (ej: stock insuficiente)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error SQLAlchemy al convertir Pedido ID {pedido_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al convertir el pedido.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado al convertir Pedido ID {pedido_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error inesperado al procesar la conversión.")
