from flask_restful import Resource
from flask_jwt_extended import jwt_required
from flask import request
from models import Almacen
from schemas import almacen_schema, almacenes_schema
from extensions import db

class AlmacenResource(Resource):
    def get(self, almacen_id=None):
        if almacen_id:
            almacen = Almacen.query.get_or_404(almacen_id)
            return almacen_schema.dump(almacen), 200
        
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        almacenes_paginados = Almacen.query.paginate(page=page, per_page=limit)
        return {
            "total": almacenes_paginados.total,
            "pagina": almacenes_paginados.page,
            "por_pagina": almacenes_paginados.per_page,
            "total_paginas": almacenes_paginados.pages,
            "data": almacenes_schema.dump(almacenes_paginados.items)
        }, 200

    @jwt_required()
    def post(self):
        nuevo_almacen = almacen_schema.load(request.get_json())
        db.session.add(nuevo_almacen)
        db.session.commit()
        return almacen_schema.dump(nuevo_almacen), 201

    @jwt_required()
    def put(self, almacen_id):
        almacen = Almacen.query.get_or_404(almacen_id)
        updated_almacen = almacen_schema.load(
            request.get_json(),
            instance=almacen,
            partial=True
        )
        db.session.commit()
        return almacen_schema.dump(updated_almacen), 200

    @jwt_required()
    def delete(self, almacen_id):
        almacen = Almacen.query.get_or_404(almacen_id)
        db.session.delete(almacen)
        db.session.commit()
        return {"message": "Almacén eliminado"}, 204