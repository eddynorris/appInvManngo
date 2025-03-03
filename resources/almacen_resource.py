from flask_restful import Resource
from flask_jwt_extended import jwt_required
from flask import request
from models import Almacen
from schemas import almacen_schema, almacenes_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE
from marshmallow import ValidationError

class AlmacenResource(Resource):
    @jwt_required()
    @handle_db_errors
    def get(self, almacen_id=None):
        if almacen_id:
            almacen = Almacen.query.get_or_404(almacen_id)
            return almacen_schema.dump(almacen), 200
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        almacenes = Almacen.query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            "data": almacenes_schema.dump(almacenes.items),
            "pagination": {
                "total": almacenes.total,
                "page": almacenes.page,
                "per_page": almacenes.per_page,
                "pages": almacenes.pages
            }
        }, 200

    @jwt_required()
    @handle_db_errors
    def post(self):
        data = almacen_schema.load(request.get_json())
        db.session.add(data)
        db.session.commit()
        return almacen_schema.dump(data), 201

    @jwt_required()
    @handle_db_errors
    def put(self, almacen_id):  
        # Obtiene el producto existente de la base de datos
        almacen = Almacen.query.get_or_404(almacen_id)
        # Deserializa los datos recibidos y actualiza la instancia del producto
        updated_almacen = almacen_schema.load(
            request.get_json(),
            instance=almacen,  # Actualiza la instancia existente
            partial=True        # Permite actualizar solo algunos campos
        )
        # Guarda los cambios en la base de datos
        db.session.commit()
        # Serializa y devuelve la respuesta
        return almacen_schema.dump(updated_almacen), 200

    @jwt_required()
    @handle_db_errors
    def delete(self, almacen_id):
        almacen = Almacen.query.get_or_404(almacen_id)
        db.session.delete(almacen)
        db.session.commit()
        return "", 204