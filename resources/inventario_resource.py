from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt
from flask import request, jsonify
from models import Inventario, PresentacionProducto, Almacen, Lote, Movimiento
from schemas import inventario_schema, inventarios_schema, lote_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE
from decimal import Decimal
import logging

# Configurar logging
logger = logging.getLogger(__name__)

class InventarioResource(Resource):
    @jwt_required()
    @handle_db_errors
    def get(self, inventario_id=None):
        try:
            if inventario_id:
                inventario = Inventario.query.get_or_404(inventario_id)
                return inventario_schema.dump(inventario), 200
            
            # Filtros: presentacion_id, almacen_id, lote_id
            filters = {
                "presentacion_id": request.args.get('presentacion_id'),
                "almacen_id": request.args.get('almacen_id'),
                "lote_id": request.args.get('lote_id')
            }
            
            query = Inventario.query
            for key, value in filters.items():
                if value:
                    query = query.filter(getattr(Inventario, key) == value)
            
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
            inventarios = query.paginate(page=page, per_page=per_page, error_out=False)
            
            return {
                "data": inventarios_schema.dump(inventarios.items),
                "pagination": {
                    "total": inventarios.total,
                    "page": inventarios.page,
                    "per_page": inventarios.per_page,
                    "pages": inventarios.pages
                }
            }, 200
        except Exception as e:
            logger.error(f"Error en GET inventario: {str(e)}")
            return {"message": "Error al obtener inventario", "details": str(e)}, 500

    @jwt_required()
    @handle_db_errors
    def post(self):
        try:
            # Verificar formato JSON
            if not request.is_json:
                return {"error": "Se esperaba contenido JSON"}, 400
                
            raw_data = request.get_json()
            if not raw_data:
                return {"error": "Datos JSON no válidos o vacíos"}, 400
            
            # Verificar campos requeridos
            required_fields = ["presentacion_id", "almacen_id", "cantidad"]
            for field in required_fields:
                if field not in raw_data:
                    return {"error": f"Campo requerido '{field}' faltante"}, 400
            
            # Validar relaciones antes de cargar el esquema
            presentacion_id = raw_data.get('presentacion_id')
            almacen_id = raw_data.get('almacen_id')
            lote_id = raw_data.get('lote_id')
            cantidad = raw_data.get('cantidad')
            
            # Verificar que los IDs son válidos
            try:
                presentacion = PresentacionProducto.query.get_or_404(presentacion_id)
                Almacen.query.get_or_404(almacen_id)
            except Exception as e:
                return {"error": f"Relación inválida: {str(e)}"}, 400
            
            # Verificar unicidad
            if Inventario.query.filter_by(
                presentacion_id=presentacion_id,
                almacen_id=almacen_id
            ).first():
                return {"error": "Registro de inventario ya existe"}, 400
            
            # Cargar con el esquema después de validaciones básicas
            data = inventario_schema.load(raw_data)
            
            # Procesar movimiento si hay cantidad inicial
            if data.cantidad > 0:
                claims = get_jwt()
                movimiento = Movimiento(
                    tipo='entrada',
                    presentacion_id=data.presentacion_id,
                    lote_id=data.lote_id,
                    cantidad=data.cantidad,
                    usuario_id=claims.get('sub'),
                    motivo="Inicialización de inventario"
                )
                db.session.add(movimiento)
                
                # Validar y actualizar lote si corresponde
                if data.lote_id and lote_id:
                    lote = Lote.query.get_or_404(lote_id)
                    
                    # Asegurar que capacidad_kg sea un Decimal para el cálculo
                    capacidad_kg = Decimal(str(presentacion.capacidad_kg))
                    cantidad_decimal = Decimal(str(data.cantidad))
                    
                    # Calcular kg a restar del lote
                    kg_a_restar = cantidad_decimal * capacidad_kg
                    
                    # Verificar stock disponible en lote
                    if not lote.cantidad_disponible_kg or lote.cantidad_disponible_kg < kg_a_restar:
                        return {"error": "Stock insuficiente en el lote"}, 400
                    
                    # Actualizar lote
                    lote.cantidad_disponible_kg -= kg_a_restar
                    
                    # No hace falta volver a cargar con lote_schema, ya actualizamos directamente
            
            # Guardar en la base de datos
            db.session.add(data)
            db.session.commit()
            return inventario_schema.dump(data), 201
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error en POST inventario: {str(e)}")
            return {"message": "Error al crear inventario", "details": str(e)}, 500

    @jwt_required()
    @handle_db_errors
    def put(self, inventario_id):
        try:
            # Verificar formato JSON
            if not request.is_json:
                return {"error": "Se esperaba contenido JSON"}, 400
                
            raw_data = request.get_json()
            if not raw_data:
                return {"error": "Datos JSON no válidos o vacíos"}, 400
            
            # Buscar el registro existente
            inventario = Inventario.query.get_or_404(inventario_id)
            
            # Validar campos inmutables antes de cargar
            immutable_fields = ["presentacion_id", "almacen_id"]
            for field in immutable_fields:
                if field in raw_data:
                    if str(raw_data[field]) != str(getattr(inventario, field)):
                        return {"error": f"Campo inmutable '{field}' no puede modificarse"}, 400

            # Capturar el lote actual y el nuevo si se está cambiando
            lote_actual_id = getattr(inventario, 'lote_id', None)
            lote_nuevo_id = raw_data.get('lote_id', lote_actual_id)

            # Si hay cambio en la cantidad, registrar movimiento y actualizar lote
            if 'cantidad' in raw_data:
                nueva_cantidad = int(raw_data['cantidad'])
                diferencia = nueva_cantidad - inventario.cantidad
                
                if diferencia != 0:
                    claims = get_jwt()
                    tipo_movimiento = 'entrada' if diferencia > 0 else 'salida'
                    cantidad_movimiento = abs(diferencia)
                    
                    # Determinar el lote a usar para el movimiento
                    lote_id_para_movimiento = lote_nuevo_id if (tipo_movimiento == 'entrada' and lote_nuevo_id != lote_actual_id) else lote_actual_id
                    
                    # Crear el movimiento con el lote correspondiente
                    movimiento = Movimiento(
                        tipo=tipo_movimiento,
                        presentacion_id=inventario.presentacion_id,
                        lote_id=lote_id_para_movimiento,
                        cantidad=cantidad_movimiento,
                        usuario_id=claims.get('sub'),
                        motivo=raw_data.get('motivo', "Ajuste manual de inventario")
                    )
                    db.session.add(movimiento)
                    
                    from decimal import Decimal
                    
                    # Obtener la presentación para calcular kg
                    presentacion = PresentacionProducto.query.get(inventario.presentacion_id)
                    
                    # CASO 1: SALIDA (disminución de inventario)
                    if tipo_movimiento == 'salida' and lote_actual_id:
                        lote_actual = Lote.query.get(lote_actual_id)
                        # No es necesario actualizar cantidad_disponible_kg para salidas,
                        # ya que la disminución de inventario no afecta el stock a granel
                    
                    # CASO 2: ENTRADA (aumento de inventario)
                    # Para entradas, siempre restar del lote (sea nuevo o actual)
                    # ya que estamos embolsando producto y reduciendo el disponible a granel
                    if tipo_movimiento == 'entrada':
                        # Determinar de qué lote restar
                        lote_para_restar = lote_nuevo_id if lote_nuevo_id != lote_actual_id else lote_actual_id
                        
                        if lote_para_restar:
                            lote = Lote.query.get(lote_para_restar)
                            if lote is not None and hasattr(lote, 'cantidad_disponible_kg'):
                                if presentacion and hasattr(presentacion, 'capacidad_kg') and presentacion.capacidad_kg:
                                    # Calcular cuánto restar del lote (embolsado)
                                    kg_a_restar = Decimal(str(presentacion.capacidad_kg)) * Decimal(str(cantidad_movimiento))
                                    
                                    # Verificar si hay suficiente cantidad disponible
                                    if lote.cantidad_disponible_kg >= kg_a_restar:
                                        lote.cantidad_disponible_kg -= kg_a_restar
                                        logger.info(f"Restando {kg_a_restar}kg del lote {lote_para_restar} por embolsado")
                                    else:
                                        # No hay suficiente cantidad disponible
                                        return {
                                            "error": f"No hay suficiente cantidad disponible en el lote. " 
                                                    f"Disponible: {lote.cantidad_disponible_kg}kg, " 
                                                    f"Requerido: {kg_a_restar}kg"
                                        }, 400
            
            # Cargar datos validados sobre la instancia existente
            updated_inventario = inventario_schema.load(
                raw_data,
                instance=inventario,
                partial=True
            )

            db.session.commit()
            return inventario_schema.dump(updated_inventario), 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error en PUT inventario: {str(e)}")
            return {"message": "Error al actualizar inventario", "details": str(e)}, 500

    @jwt_required()
    @handle_db_errors
    def delete(self, inventario_id):
        try:
            inventario = Inventario.query.get_or_404(inventario_id)
            
            # Verificar movimientos asociados
            # Nota: Aquí asumimos que hay una relación inversa desde Movimiento hacia Inventario
            # Si no es así, esta verificación debería ajustarse
            movimientos = Movimiento.query.filter_by(presentacion_id=inventario.presentacion_id, 
                                                     lote_id=inventario.lote_id).all()
            
            if movimientos:
                return {"error": "No se puede eliminar un inventario con movimientos registrados"}, 400
            
            db.session.delete(inventario)
            db.session.commit()
            return {"message": "Presentación en Inventario eliminada con éxito"}, 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error en DELETE inventario: {str(e)}")
            return {"message": "Error al eliminar inventario", "details": str(e)}, 500