from flask_restful import Resource
from flask_jwt_extended import jwt_required
from flask import request
from models import Proveedor
from schemas import proveedor_schema, proveedores_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE

class ProveedorResource(Resource):
    @jwt_required()
    def get(self, proveedor_id=None):
        if proveedor_id:
            proveedor = Proveedor.query.get_or_404(proveedor_id)
            return proveedor_schema().dump(proveedor), 200
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        proveedores = Proveedor.query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            "data": proveedor_schema.dump(proveedores.items),
            "pagination": {
                "total": proveedores.total,
                "page": proveedores.page,
                "per_page": proveedores.per_page,
                "pages": proveedores.pages            
            }        
        }, 200

    @jwt_required()
    def post(self):

        nuevo_proveedor = proveedor_schema.load(request.get_json())
        db.session.add(nuevo_proveedor)
        db.session.commit()
        return proveedor_schema.dump(nuevo_proveedor), 201

    @jwt_required()
    def put(self, proveedor_id):
        proveedor = Proveedor.query.get_or_404(proveedor_id)
        updated_proveedor = proveedor_schema.load(
            request.get_json(),
            instance=proveedor,
            partial=True
        )
        db.session.commit()
        return proveedor_schema.dump(updated_proveedor), 200

    @jwt_required()
    def delete(self, proveedor_id):
        proveedor = Proveedor.query.get_or_404(proveedor_id)
        db.session.delete(proveedor)
        db.session.commit()
        return {"message": "Proveedor eliminado"}, 204