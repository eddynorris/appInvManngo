from flask_restful import Resource
from flask_jwt_extended import jwt_required
from flask import request
from models import Movimiento
from schemas import movimiento_schema, movimientos_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE

class MovimientoResource(Resource):
    @jwt_required()
    @handle_db_errors
    def get(self, movimiento_id=None):
        if movimiento_id:
            movimiento = Movimiento.query.get_or_404(movimiento_id)
            return movimiento_schema.dump(movimiento), 200
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        movimientos = Movimiento.query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            "data": movimientos_schema.dump(movimientos.items),
            "pagination": {
                "total": movimientos.total,
                "page": movimientos.page,
                "per_page": movimientos.per_page,
                "pages": movimientos.pages
            }
        }, 200

    @jwt_required()
    @handle_db_errors
    def post(self):
        nuevo_movimiento = movimiento_schema.load(request.get_json())
        db.session.add(nuevo_movimiento)
        db.session.commit()
        return movimiento_schema.dump(nuevo_movimiento), 201

    @jwt_required()
    @handle_db_errors
    def put(self, movimiento_id):
        movimiento = Movimiento.query.get_or_404(movimiento_id)
        updated_movimiento = movimiento_schema.load(
            request.get_json(),
            instance=movimiento,
            partial=True
        )
        db.session.commit()
        return movimiento_schema.dump(updated_movimiento), 200

    @jwt_required()
    @handle_db_errors
    def delete(self, movimiento_id):
        movimiento = Movimiento.query.get_or_404(movimiento_id)
        db.session.delete(movimiento)
        db.session.commit()
        return {"message": "Movimiento eliminado"}, 204