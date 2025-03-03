from flask_restful import Resource
from flask_jwt_extended import jwt_required
from flask import request
from models import Gasto
from schemas import gasto_schema, gastos_schema
from extensions import db
from marshmallow import ValidationError
from common import handle_db_errors, MAX_ITEMS_PER_PAGE

class GastoResource(Resource):
    @jwt_required()
    @handle_db_errors
    def get(self, gasto_id=None):
        if gasto_id:
            gasto = Gasto.query.get_or_404(gasto_id)
            return gasto_schema.dump(gasto), 200
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        gastos = Gasto.query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            "data": gastos_schema.dump(gastos.items),
            "pagination": {
                "total": gastos.total,
                "page": gastos.page,
                "per_page": gastos.per_page,
                "pages": gastos.pages
            }
        }, 200

    @jwt_required()
    @handle_db_errors
    def post(self):
        nuevo_gasto = gasto_schema.load(request.get_json())
        db.session.add(nuevo_gasto)
        db.session.commit()
        return gasto_schema.dump(nuevo_gasto), 201

    @jwt_required()
    @handle_db_errors
    def put(self, gasto_id):
        gasto = Gasto.query.get_or_404(gasto_id)

        updated_gasto = gasto_schema.load(
            request.get_json(),
            instance=gasto, 
            partial=True        
        )
        db.session.commit()
        return gasto_schema.dump(updated_gasto), 200

    @jwt_required()
    @handle_db_errors
    def delete(self, gasto_id):
        gasto = Gasto.query.get_or_404(gasto_id)
        db.session.delete(gasto)
        db.session.commit()
        return "", 204