from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt
from flask import request
from models import Inventario, PresentacionProducto, Almacen, Lote, Movimiento
from schemas import inventario_schema, inventarios_schema, lote_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE

class InventarioResource(Resource):
    @jwt_required()
    @handle_db_errors
    def get(self, inventario_id=None):
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
        inventarios = query.paginate(page=page, per_page=per_page)
        
        return {
            "data": inventarios_schema.dump(inventarios.items),
            "pagination": {
                "total": inventarios.total,
                "page": inventarios.page,
                "per_page": inventarios.per_page,
                "pages": inventarios.pages
            }
        }, 200

    @jwt_required()
    @handle_db_errors
    def post(self):
        data = inventario_schema.load(request.get_json())
        
        # Validar relaciones
        presentacion = PresentacionProducto.query.get_or_404(data.presentacion_id)
        Almacen.query.get_or_404(data.almacen_id)
        
        # Verificar unicidad
        if Inventario.query.filter_by(
            presentacion_id=data.presentacion_id,
            almacen_id=data.almacen_id
        ).first():
            return {"error": "Registro de inventario ya existe"}, 400
        
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
            
            if data.lote_id:
                lote = Lote.query.get_or_404(data.lote_id)

                # Calcular kg a restar del lote
                kg_a_restar = data.cantidad * presentacion.capacidad_kg

                # Verificar que hay suficiente stock en el lote
                if lote.cantidad_disponible_kg < kg_a_restar:
                    return {"error": "Stock insuficiente en el lote"}, 400

                lote.cantidad_disponible_kg -= kg_a_restar
                #Actualizar Lote
                lote_schema.load(
                request.get_json(),
                instance=lote,
                partial=True
                )

        db.session.add(data)
        db.session.commit()
        return inventario_schema.dump(data), 201

    @jwt_required()
    @handle_db_errors
    def put(self, inventario_id):
        
        inventario = Inventario.query.get_or_404(inventario_id)
        # Obtener datos en crudo para validación
        raw_data = request.get_json()

        # Validar campos inmutables antes de cargar
        immutable_fields = ["presentacion_id", "almacen_id"]
        for field in immutable_fields:
            if field in raw_data:
                if str(raw_data[field]) != str(getattr(inventario, field)):
                    return {"error": f"Campo inmutable '{field}' no puede modificarse"}, 400

        # Cargar datos validados sobre la instancia existente
        updated_inventario = inventario_schema.load(
            raw_data,
            instance=inventario,
            partial=True
        )

        db.session.commit()
        return inventario_schema.dump(updated_inventario), 200

    @jwt_required()
    @handle_db_errors
    def delete(self, inventario_id):
        inventario = Inventario.query.get_or_404(inventario_id)
        # Verificar movimientos asociados
        if inventario.movimientos:
            return {"error": "No se puede eliminar un inventario con movimientos registrados"}, 400
        
        db.session.delete(inventario)
        db.session.commit()
        return "Presentacion en Inventario Eliminado", 200