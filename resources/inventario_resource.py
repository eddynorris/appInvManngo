from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt
from flask import request
from models import Inventario, PresentacionProducto, Almacen, Lote
from schemas import inventario_schema, inventarios_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE

class InventarioResource(Resource):
    @jwt_required()
    @handle_db_errors
    def get(self, inventario_id=None):
        if inventario_id:
            inventario = Inventario.query.get_or_404(inventario_id)
            return inventario_schema.dump(inventario), 200
        
        # Filtros: producto_id, presentacion_id, almacen_id, lote_id
        filters = {
            "producto_id": request.args.get('producto_id'),
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
        PresentacionProducto.query.get_or_404(data["presentacion_id"])
        Almacen.query.get_or_404(data["almacen_id"])
        if data.get("lote_id"):
            Lote.query.get_or_404(data["lote_id"])
        
        # Verificar unicidad
        if Inventario.query.filter_by(
            producto_id=data["producto_id"],
            presentacion_id=data["presentacion_id"],
            almacen_id=data["almacen_id"]
        ).first():
            return {"error": "Registro de inventario ya existe"}, 400
        
        nuevo_inventario = Inventario(**data)
        db.session.add(nuevo_inventario)
        db.session.commit()
        return inventario_schema.dump(nuevo_inventario), 201

    @jwt_required()
    @handle_db_errors
    def put(self, inventario_id):
        inventario = Inventario.query.get_or_404(inventario_id)
        data = inventario_schema.load(request.get_json(), partial=True)
        
        # Validar campos inmutables
        immutable_fields = ["producto_id", "presentacion_id", "almacen_id"]
        for field in immutable_fields:
            if field in data and data[field] != getattr(inventario, field):
                return {"error": f"No se puede modificar el campo '{field}'"}, 400
        
        # Actualizar campos permitidos
        for key, value in data.items():
            setattr(inventario, key, value)
        
        db.session.commit()
        return inventario_schema.dump(inventario), 200

    @jwt_required()
    @handle_db_errors
    def delete(self, inventario_id):
        inventario = Inventario.query.get_or_404(inventario_id)
        
        # Verificar movimientos asociados
        if inventario.movimientos:
            return {"error": "No se puede eliminar un inventario con movimientos registrados"}, 400
        
        db.session.delete(inventario)
        db.session.commit()
        return "", 204