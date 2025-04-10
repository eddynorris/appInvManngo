from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt
from flask import request, current_app
from models import Venta, VentaDetalle, Inventario, Cliente, PresentacionProducto, Almacen, Movimiento
from schemas import venta_schema, ventas_schema, venta_detalle_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE, mismo_almacen_o_admin, validate_pagination_params, create_pagination_response
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import logging

# Configurar logging
logger = logging.getLogger(__name__)

class VentaResource(Resource):
    @jwt_required()
    @handle_db_errors
    def get(self, venta_id=None):
        """
        Obtiene venta(s)
        - Con ID: Detalle completo de la venta
        - Sin ID: Lista paginada con filtros
        """
        try:
            # Si se solicita una venta específica
            if venta_id:
                venta = Venta.query.get_or_404(venta_id)
                # Verificar permisos (solo admin o usuario del mismo almacén)
                claims = get_jwt()
                if claims.get('rol') != 'admin' and venta.almacen_id != claims.get('almacen_id'):
                    return {"error": "No tiene permisos para ver esta venta"}, 403
                
                return venta_schema.dump(venta), 200
            
            # Construir query con filtros
            query = Venta.query
            
            # Aplicar restricción por almacén para usuarios no admin
            claims = get_jwt()
            if claims.get('rol') != 'admin':
                almacen_id = claims.get('almacen_id')
                if not almacen_id:
                    return {"error": "Usuario sin almacén asignado"}, 400
                query = query.filter_by(almacen_id=almacen_id)
            
            # Aplicar filtros adicionales
            if cliente_id := request.args.get('cliente_id'):
                try:
                    query = query.filter_by(cliente_id=int(cliente_id))
                except ValueError:
                    return {"error": "ID de cliente inválido"}, 400
                    
            if almacen_id := request.args.get('almacen_id'):
                # Para admins que quieren filtrar por almacén específico
                if claims.get('rol') == 'admin':
                    try:
                        query = query.filter_by(almacen_id=int(almacen_id))
                    except ValueError:
                        return {"error": "ID de almacén inválido"}, 400
                        
            if vendedor_id := request.args.get('vendedor_id'):
                try:
                    query = query.filter_by(vendedor_id=int(vendedor_id))
                except ValueError:
                    return {"error": "ID de vendedor inválido"}, 400
            
            # Filtro por rango de fechas
            fecha_inicio = request.args.get('fecha_inicio')
            fecha_fin = request.args.get('fecha_fin')
            
            if fecha_inicio and fecha_fin:
                try:
                    fecha_inicio = datetime.fromisoformat(fecha_inicio.replace('Z', '+00:00'))
                    fecha_fin = datetime.fromisoformat(fecha_fin.replace('Z', '+00:00'))
                    query = query.filter(Venta.fecha.between(fecha_inicio, fecha_fin))
                except ValueError:
                    return {"error": "Formato de fecha inválido. Use ISO 8601 (YYYY-MM-DDTHH:MM:SS)"}, 400
            
            # Ordenación
            orden = request.args.get('orden', 'desc')
            if orden.lower() == 'asc':
                query = query.order_by(Venta.fecha.asc())
            else:
                query = query.order_by(Venta.fecha.desc())
            
            # Paginación con validación
            page, per_page = validate_pagination_params()
            ventas = query.paginate(page=page, per_page=per_page)
            
            # Respuesta estandarizada
            return create_pagination_response(ventas_schema.dump(ventas.items), ventas), 200
            
        except Exception as e:
            logger.error(f"Error al obtener ventas: {str(e)}")
            return {"error": "Error al procesar la solicitud"}, 500

    @jwt_required()
    @mismo_almacen_o_admin
    @handle_db_errors
    def post(self):
        """Crea una nueva venta con validación completa"""
        try:
            # Validar formato de entrada
            if not request.is_json:
                return {"error": "Se esperaba contenido JSON"}, 400
                
            data = request.get_json()
            if not data:
                return {"error": "Datos JSON vacíos o inválidos"}, 400
            
            # Validaciones preliminares
            if not data.get('cliente_id'):
                return {"error": "Se requiere ID de cliente"}, 400
                
            if not data.get('almacen_id'):
                return {"error": "Se requiere ID de almacén"}, 400
                
            if not data.get('detalles') or not isinstance(data.get('detalles'), list) or len(data.get('detalles')) == 0:
                return {"error": "Se requiere al menos un detalle de venta"}, 400
            
            # Cargar datos validados con schema
            venta_data = venta_schema.load(data)
            
            # Verificar existencia de cliente y almacén
            cliente = Cliente.query.get_or_404(venta_data.cliente_id)
            almacen = Almacen.query.get_or_404(venta_data.almacen_id)
            
            # Asignar vendedor desde JWT
            claims = get_jwt()
            venta_data.vendedor_id = int(claims.get('sub'))
            
            # Procesar detalles de venta
            total = Decimal('0')
            inventarios_a_actualizar = {}
            movimientos = []
            
            for detalle in venta_data.detalles:
                # Verificar presentación
                presentacion = PresentacionProducto.query.get_or_404(detalle.presentacion_id)
                
                # Verificar inventario
                inventario = Inventario.query.filter_by(
                    presentacion_id=presentacion.id,
                    almacen_id=venta_data.almacen_id
                ).first()
                
                if not inventario:
                    return {"error": f"La presentación {presentacion.nombre} no está disponible en este almacén"}, 400
                
                if inventario.cantidad < detalle.cantidad:
                    return {
                        "error": f"Stock insuficiente para {presentacion.nombre}",
                        "disponible": inventario.cantidad,
                        "solicitado": detalle.cantidad
                    }, 400
                
                # Asignar precio unitario si no viene
                if not hasattr(detalle, 'precio_unitario') or not detalle.precio_unitario:
                    detalle.precio_unitario = presentacion.precio_venta
                
                # Validar precio unitario (evitar valores negativos o cero)
                if detalle.precio_unitario <= 0:
                    return {"error": f"Precio unitario inválido para {presentacion.nombre}"}, 400
                
                # Registrar datos para el movimiento
                movimientos.append({
                    "presentacion_id": presentacion.id,
                    "lote_id": inventario.lote_id,
                    "cantidad": detalle.cantidad
                })
                
                # Calcular subtotal
                subtotal = detalle.cantidad * detalle.precio_unitario
                total += subtotal
                
                # Marcar inventario para actualización
                inventarios_a_actualizar[presentacion.id] = (inventario, detalle.cantidad)
            
            # Crear venta
            nueva_venta = Venta(
                cliente_id=venta_data.cliente_id,
                almacen_id=venta_data.almacen_id,
                vendedor_id=venta_data.vendedor_id,
                total=total,
                tipo_pago=venta_data.tipo_pago,
                consumo_diario_kg=venta_data.consumo_diario_kg,
                detalles=venta_data.detalles
            )
            
            try:
                # Iniciar transacción
                db.session.add(nueva_venta)
                db.session.flush()  # Generamos el ID de la venta
                
                # Crear movimientos después de obtener el ID de la venta
                for movimiento_data in movimientos:
                    movimiento = Movimiento(
                        tipo='salida',
                        presentacion_id=movimiento_data["presentacion_id"],
                        lote_id=movimiento_data["lote_id"],
                        cantidad=movimiento_data["cantidad"],
                        usuario_id=claims.get('sub'),
                        motivo=f"Venta ID: {nueva_venta.id} - Cliente: {cliente.nombre}"
                    )
                    db.session.add(movimiento)
                
                # Actualizar inventarios
                for inventario, cantidad in inventarios_a_actualizar.values():
                    inventario.cantidad -= cantidad
                    inventario.ultima_actualizacion = datetime.now(timezone.utc)
                
                # Actualizar proyección del cliente
                if nueva_venta.consumo_diario_kg:
                    if Decimal(nueva_venta.consumo_diario_kg) <= 0:
                        raise ValueError("El consumo diario debe ser mayor a 0")
                    
                    cliente.ultima_fecha_compra = datetime.now(timezone.utc)
                    cliente.frecuencia_compra_dias = (total / Decimal(nueva_venta.consumo_diario_kg)).quantize(Decimal('1.00'))
                
                # Confirmar cambios
                db.session.commit()
                
                logger.info(f"Venta creada: ID {nueva_venta.id}, Cliente: {cliente.nombre}, Total: {total}")
                return venta_schema.dump(nueva_venta), 201
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error al procesar venta: {str(e)}")
                return {"error": f"Error al crear la venta: {str(e)}"}, 500
                
        except Exception as e:
            logger.error(f"Error al crear venta: {str(e)}")
            return {"error": "Error al procesar la solicitud"}, 500

    @jwt_required()
    @mismo_almacen_o_admin
    @handle_db_errors
    def put(self, venta_id):
        """Actualiza una venta existente (campos limitados)"""
        try:
            if not venta_id:
                return {"error": "Se requiere ID de venta"}, 400
            
            venta = Venta.query.get_or_404(venta_id)
            
            # Validar formato de entrada
            if not request.is_json:
                return {"error": "Se esperaba contenido JSON"}, 400
                
            raw_data = request.get_json()
            if not raw_data:
                return {"error": "Datos JSON vacíos o inválidos"}, 400
            
            # Validar campos inmutables
            campos_inmutables = ["detalles", "almacen_id", "cliente_id", "fecha", "total"]
            for campo in campos_inmutables:
                if campo in raw_data:
                    return {
                        "error": f"No se puede modificar el campo '{campo}'", 
                        "mensaje": "Para modificar detalles de venta, use los endpoints específicos"
                    }, 400
            
            # Actualizar venta
            updated_venta = venta_schema.load(
                raw_data,
                instance=venta,
                partial=True
            )
            
            db.session.commit()
            logger.info(f"Venta actualizada: ID {venta_id}")
            return venta_schema.dump(updated_venta), 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al actualizar venta: {str(e)}")
            return {"error": "Error al actualizar la venta"}, 500

    @jwt_required()
    @mismo_almacen_o_admin
    @handle_db_errors
    def delete(self, venta_id):
        """Elimina una venta y revierte inventario"""
        try:
            if not venta_id:
                return {"error": "Se requiere ID de venta"}, 400
                
            venta = Venta.query.get_or_404(venta_id)
            
            # Verificar si tiene pagos asociados
            if venta.pagos and len(venta.pagos) > 0:
                return {
                    "error": "No se puede eliminar una venta con pagos registrados", 
                    "pagos": len(venta.pagos)
                }, 400
            
            try:
                # Revertir movimientos e inventario
                movimientos = Movimiento.query.filter(
                    Movimiento.motivo.like(f"Venta ID: {venta_id}%")
                ).all()
                
                for movimiento in movimientos:
                    # Validar que el movimiento sea de tipo 'salida'
                    if movimiento.tipo != 'salida':
                        continue
                    
                    inventario = Inventario.query.filter_by(
                        presentacion_id=movimiento.presentacion_id,
                        almacen_id=venta.almacen_id
                    ).first()
                    
                    if inventario:
                        inventario.cantidad += movimiento.cantidad
                        inventario.ultima_actualizacion = datetime.now(timezone.utc)
                    
                    db.session.delete(movimiento)
                
                # Guardar información para el log
                cliente_nombre = venta.cliente.nombre if venta.cliente else "Desconocido"
                venta_total = venta.total
                
                # Eliminar venta
                db.session.delete(venta)
                db.session.commit()
                
                logger.info(f"Venta eliminada: ID {venta_id}, Cliente: {cliente_nombre}, Total: {venta_total}")
                return {"message": "Venta eliminada con éxito"}, 200
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error al eliminar venta: {str(e)}")
                return {"error": str(e)}, 500
                
        except Exception as e:
            logger.error(f"Error al eliminar venta: {str(e)}")
            return {"error": "Error al procesar la solicitud"}, 500