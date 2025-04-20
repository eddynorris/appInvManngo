# app/services/service_venta.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from app import models, schemas, crud
from decimal import Decimal
from datetime import datetime, timezone
import logging # Usar logging en lugar de print
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Venta

logger = logging.getLogger(__name__)

def create_venta_with_details(db: Session, venta_in: schemas.VentaCreate, vendedor_id: int) -> "Venta":
    """
    Crea una venta, sus detalles, actualiza inventario y crea movimientos.
    Maneja la transacción completa.
    """
    venta_detalles_in = venta_in.detalles
    venta_base_data = venta_in.model_dump(exclude={'detalles'})

    # Validaciones previas (podrían moverse a la capa API si son simples)
    cliente = crud.crud_cliente.get_cliente(db, venta_in.cliente_id)
    if not cliente:
        logger.warning(f"Intento de crear venta para cliente inexistente: ID {venta_in.cliente_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cliente ID {venta_in.cliente_id} no encontrado.")
    almacen = crud.crud_almacen.get_almacen(db, venta_in.almacen_id)
    if not almacen:
        logger.warning(f"Intento de crear venta para almacén inexistente: ID {venta_in.almacen_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Almacén ID {venta_in.almacen_id} no encontrado.")

    total_venta_calculado = Decimal('0')
    detalles_orm = []
    inventarios_a_actualizar = {} # {presentacion_id: (inventario_obj, cantidad_a_restar)}
    movimientos_a_crear_data = [] # Guardar datos para crear movimientos

    # 1. Validar stock y preparar datos (dentro de la sesión para bloqueo)
    for detalle_in in venta_detalles_in:
        presentacion = crud.crud_presentacion.get_presentacion(db, detalle_in.presentacion_id)
        if not presentacion or not presentacion.activo:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Presentación ID {detalle_in.presentacion_id} no válida o inactiva.")

        # Bloquear fila de inventario para evitar condiciones de carrera
        inventario = db.query(models.Inventario).filter(
             models.Inventario.presentacion_id == detalle_in.presentacion_id,
             models.Inventario.almacen_id == venta_in.almacen_id
         ).with_for_update().first()

        if not inventario or inventario.cantidad < detalle_in.cantidad:
            disponible = inventario.cantidad if inventario else 0
            logger.warning(f"Stock insuficiente: Pres={presentacion.id}, Alm={almacen.id}, Disp={disponible}, Sol={detalle_in.cantidad}")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Stock insuficiente para '{presentacion.nombre}'. Disponible: {disponible}")

        precio_unitario = detalle_in.precio_unitario
        total_linea = detalle_in.cantidad * precio_unitario
        total_venta_calculado += total_linea

        detalles_orm.append(models.VentaDetalle(
            presentacion_id=detalle_in.presentacion_id,
            cantidad=detalle_in.cantidad,
            precio_unitario=precio_unitario
        ))

        inventarios_a_actualizar[presentacion.id] = (inventario, detalle_in.cantidad)

        movimientos_a_crear_data.append({
             "tipo": 'salida',
             "presentacion_id": presentacion.id,
             "lote_id": inventario.lote_id,
             "cantidad": Decimal(detalle_in.cantidad),
             "motivo_base": f"Venta - Cliente: {cliente.nombre}"
         })

    # --- Inicio Transacción ---
    try:
        # 2. Crear la venta principal
        db_venta = models.Venta(
            **venta_base_data,
            vendedor_id=vendedor_id,
            total=total_venta_calculado,
            detalles=detalles_orm,
            estado_pago='pendiente' # Asegurar estado inicial
        )
        db.add(db_venta)
        db.flush() # Obtener ID venta

        venta_id = db_venta.id # Guardar ID para motivo

        # 3. Crear movimientos (ahora usa crud.crud_movimiento)
        for mov_data in movimientos_a_crear_data:
            mov_create = schemas.MovimientoCreate(
                tipo=mov_data["tipo"],
                presentacion_id=mov_data["presentacion_id"],
                lote_id=mov_data["lote_id"],
                cantidad=mov_data["cantidad"],
                motivo=f"Venta ID: {venta_id} - {mov_data['motivo_base']}"
            )
            # Crear movimiento sin commit individual
            mov_obj = crud.crud_movimiento.create_movimiento(db, mov_create, usuario_id=vendedor_id)
            db.add(mov_obj) # Añadir a la sesión actual

        # 4. Actualizar inventarios
        for inv, cantidad_vendida in inventarios_a_actualizar.values():
            inv.cantidad -= cantidad_vendida
            # No es necesario db.add(inv) si ya está en sesión y fue bloqueado

        # 5. Actualizar proyección del cliente (si aplica)
        if venta_in.consumo_diario_kg and venta_in.consumo_diario_kg > 0:
             if cliente:
                 cliente.ultima_fecha_compra = datetime.now(timezone.utc)
                 try:
                     if Decimal(venta_in.consumo_diario_kg) > 0:
                          cliente.frecuencia_compra_dias = int(round(total_venta_calculado / Decimal(venta_in.consumo_diario_kg)))
                 except Exception as calc_err:
                      logger.error(f"Error calculando frecuencia compra cliente {cliente.id}: {calc_err}")
                 # No es necesario db.add(cliente) si ya está en sesión

        db.commit() # Commit de toda la transacción
        db.refresh(db_venta) # Refrescar para obtener estado final
        logger.info(f"Venta ID {venta_id} creada exitosamente por Vendedor ID {vendedor_id}")
        return db_venta

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error SQLAlchemy al crear venta (Vendedor ID {vendedor_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al guardar la venta.")
    except Exception as e: # Captura otras excepciones inesperadas
        db.rollback()
        logger.error(f"Error inesperado al crear venta (Vendedor ID {vendedor_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error inesperado al procesar la venta.")


def delete_venta_and_reverse(db: Session, venta_id: int, current_user_id: int) -> "Venta":
    """Elimina una venta, revierte movimientos y restaura inventario."""
    venta = crud.crud_venta.get_venta(db, venta_id)
    if not venta:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Venta ID {venta_id} no encontrada.")

    # --- Inicio Transacción ---
    try:
        # 1. Identificar movimientos de salida asociados a esta venta
        motivo_like = f"Venta ID: {venta.id}%"
        movimientos_salida = db.query(models.Movimiento).filter(
            models.Movimiento.motivo.like(motivo_like),
            models.Movimiento.tipo == 'salida'
        ).all()

        inventarios_a_restaurar = {} # {presentacion_id: cantidad_a_sumar}

        # 2. Preparar reversión de inventario y eliminar movimientos originales
        for mov in movimientos_salida:
            # Acumular cantidad a restaurar por presentación
            cantidad_decimal = Decimal(mov.cantidad)
            inventarios_a_restaurar[mov.presentacion_id] = inventarios_a_restaurar.get(mov.presentacion_id, Decimal(0)) + cantidad_decimal

            # Crear movimiento de entrada para auditoría de la reversión
            mov_reversion = models.Movimiento(
                tipo='entrada',
                presentacion_id=mov.presentacion_id,
                lote_id=mov.lote_id,
                usuario_id=current_user_id,
                cantidad=mov.cantidad, # Mantener tipo original
                motivo=f"Reversión Venta ID: {venta.id}"
            )
            db.add(mov_reversion)
            db.delete(mov) # Eliminar el movimiento original

        # 3. Restaurar cantidades en inventario
        for presentacion_id, cantidad_a_sumar in inventarios_a_restaurar.items():
            inventario = db.query(models.Inventario).filter(
                 models.Inventario.presentacion_id == presentacion_id,
                 models.Inventario.almacen_id == venta.almacen_id
             ).with_for_update().first() # Bloquear fila

            if inventario:
                inventario.cantidad += int(round(cantidad_a_sumar)) # Asumiendo inventario es int
                # No se necesita db.add() si ya está en sesión
            else:
                logger.warning(f"Inventario no encontrado para restaurar Venta ID {venta_id}, Pres ID {presentacion_id}, Alm ID {venta.almacen_id}")
                # Considerar crear el registro de inventario aquí si es necesario

        # 4. Eliminar Pagos asociados (si existen)
        pagos = db.query(models.Pago).filter(models.Pago.venta_id == venta.id).all()
        for pago in pagos:
            db.delete(pago)

        # 5. Eliminar la Venta (detalles se eliminan por cascade)
        db.delete(venta)
        db.commit() # Commit de toda la transacción
        logger.info(f"Venta ID {venta_id} eliminada y revertida por Usuario ID {current_user_id}")
        # No se puede refrescar venta, ya no existe
        return venta # Devolver el objeto antes de eliminarlo (opcional)

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error SQLAlchemy al eliminar/revertir venta ID {venta_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al eliminar la venta.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado al eliminar/revertir venta ID {venta_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error inesperado al procesar la eliminación.")
