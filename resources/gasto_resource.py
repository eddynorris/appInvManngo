from flask_restful import Resource
from flask_jwt_extended import jwt_required
from flask import request
from models import Gasto
from schemas import gasto_schema, gastos_schema
from extensions import db

class GastoResource(Resource):
    def get(self, gasto_id=None):
        if gasto_id:
            gasto = Gasto.query.get_or_404(gasto_id)
            return gasto_schema.dump(gasto), 200
        
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        gastos_paginados = Gasto.query.paginate(page=page, per_page=limit)
        return {
            "total": gastos_paginados.total,
            "pagina": gastos_paginados.page,
            "por_pagina": gastos_paginados.per_page,
            "total_paginas": gastos_paginados.pages,
            "data": gastos_schema.dump(gastos_paginados.items)
        }, 200

    @jwt_required()
    def post(self):
        nuevo_gasto = gasto_schema.load(request.get_json())
        db.session.add(nuevo_gasto)
        db.session.commit()
        return gasto_schema.dump(nuevo_gasto), 201

    @jwt_required()
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
    def delete(self, gasto_id):
        gasto = Gasto.query.get_or_404(gasto_id)
        db.session.delete(gasto)
        db.session.commit()
        return {"message": "Gasto eliminado"}, 204