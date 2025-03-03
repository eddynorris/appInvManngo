from flask_restful import Resource
from flask_jwt_extended import jwt_required
from flask import request
from models import Almacen
from schemas import almacen_schema, almacenes_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE

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
        almacen = Almacen.query.get_or_404(almacen_id)
        data = almacen_schema.load(request.get_json(), partial=True)
        
        for key, value in data.items():
            setattr(almacen, key, value)
            
        db.session.commit()
        return almacen_schema.dump(almacen), 200

    @jwt_required()
    @handle_db_errors
    def delete(self, almacen_id):
        almacen = Almacen.query.get_or_404(almacen_id)
        db.session.delete(almacen)
        db.session.commit()
        return "", 204