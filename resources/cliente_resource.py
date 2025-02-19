from flask_restful import Resource
from flask_jwt_extended import jwt_required
from flask import request
from models import Cliente
from schemas import cliente_schema, clientes_schema
from extensions import db

class ClienteResource(Resource):
    def get(self, cliente_id=None):
        if cliente_id:
            cliente = Cliente.query.get_or_404(cliente_id)
            return cliente_schema.dump(cliente), 200
        
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        clientes_paginados = Cliente.query.paginate(page=page, per_page=limit)
        return {
            "total": clientes_paginados.total,
            "pagina": clientes_paginados.page,
            "por_pagina": clientes_paginados.per_page,
            "total_paginas": clientes_paginados.pages,
            "data": clientes_schema.dump(clientes_paginados.items)
        }, 200

    @jwt_required()
    def post(self):
        nuevo_cliente = cliente_schema.load(request.get_json())
        db.session.add(nuevo_cliente)
        db.session.commit()
        return cliente_schema.dump(nuevo_cliente), 201

    @jwt_required()
    def put(self, cliente_id):
        cliente = Cliente.query.get_or_404(cliente_id)
        updated_cliente = cliente_schema.load(
            request.get_json(),
            instance=cliente,
            partial=True
        )
        db.session.commit()
        return cliente_schema.dump(updated_cliente), 200

    @jwt_required()
    def delete(self, cliente_id):
        cliente = Cliente.query.get_or_404(cliente_id)
        db.session.delete(cliente)
        db.session.commit()
        return {"message": "Cliente eliminado"}, 204