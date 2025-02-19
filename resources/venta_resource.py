from flask_restful import Resource
from flask_jwt_extended import jwt_required
from flask import request
from models import Venta
from schemas import venta_schema, ventas_schema
from extensions import db

class VentaResource(Resource):
    def get(self, venta_id=None):
        if venta_id:
            venta = Venta.query.get_or_404(venta_id)
            return venta_schema.dump(venta), 200
        
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        ventas_paginadas = Venta.query.paginate(page=page, per_page=limit)
        return {
            "total": ventas_paginadas.total,
            "pagina": ventas_paginadas.page,
            "por_pagina": ventas_paginadas.per_page,
            "total_paginas": ventas_paginadas.pages,
            "data": ventas_schema.dump(ventas_paginadas.items)
        }, 200

    @jwt_required()
    def post(self):
        nueva_venta = venta_schema.load(request.get_json())
        db.session.add(nueva_venta)
        db.session.commit()
        return venta_schema.dump(nueva_venta), 201

    @jwt_required()
    def put(self, venta_id):
        venta = Venta.query.get_or_404(venta_id)
        updated_venta = venta_schema.load(
            request.get_json(),
            instance=venta,
            partial=True
        )
        db.session.commit()
        return venta_schema.dump(updated_venta), 200

    @jwt_required()
    def delete(self, venta_id):
        venta = Venta.query.get_or_404(venta_id)
        db.session.delete(venta)
        db.session.commit()
        return {"message": "Venta eliminada"}, 204