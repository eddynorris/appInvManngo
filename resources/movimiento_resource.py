from flask_restful import Resource
from flask_jwt_extended import jwt_required
from flask import request
from models import Movimiento
from schemas import movimiento_schema, movimientos_schema
from extensions import db

class MovimientoResource(Resource):
    def get(self, movimiento_id=None):
        if movimiento_id:
            movimiento = Movimiento.query.get_or_404(movimiento_id)
            return movimiento_schema.dump(movimiento), 200
        
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        movimientos_paginados = Movimiento.query.paginate(page=page, per_page=limit)
        return {
            "total": movimientos_paginados.total,
            "pagina": movimientos_paginados.page,
            "por_pagina": movimientos_paginados.per_page,
            "total_paginas": movimientos_paginados.pages,
            "data": movimientos_schema.dump(movimientos_paginados.items)
        }, 200

    @jwt_required()
    def post(self):
        nuevo_movimiento = movimiento_schema.load(request.get_json())
        db.session.add(nuevo_movimiento)
        db.session.commit()
        return movimiento_schema.dump(nuevo_movimiento), 201

    @jwt_required()
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
    def delete(self, movimiento_id):
        movimiento = Movimiento.query.get_or_404(movimiento_id)
        db.session.delete(movimiento)
        db.session.commit()
        return {"message": "Movimiento eliminado"}, 204