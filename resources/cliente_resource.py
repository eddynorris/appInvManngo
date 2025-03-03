from flask_restful import Resource, abort
from flask_jwt_extended import jwt_required
from flask import request
from models import Cliente, Producto
from schemas import cliente_schema, clientes_schema, producto_schema, productos_schema
from extensions import db
from marshmallow import ValidationError
from common import handle_db_errors, MAX_ITEMS_PER_PAGE

class ClienteResource(Resource):
    @jwt_required()
    @handle_db_errors
    def get(self, cliente_id=None):
        if cliente_id:
            cliente = Cliente.query.get_or_404(cliente_id)
            return cliente_schema.dump(cliente), 200
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        
        clientes = Cliente.query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            "data": clientes_schema.dump(clientes.items),
            "pagination": {
                "total": clientes.total,
                "page": clientes.page,
                "per_page": clientes.per_page,
                "pages": clientes.pages
            }
        }, 200

    @jwt_required()
    @handle_db_errors
    def post(self):
        data = cliente_schema.load(request.get_json())
        db.session.add(data)
        db.session.commit()
        
        return cliente_schema.dump(data), 201

    @jwt_required()
    @handle_db_errors
    def put(self, cliente_id):
        # Obtiene el producto existente de la base de datos
        cliente = Cliente.query.get_or_404(cliente_id)
        # Deserializa los datos recibidos y actualiza la instancia del producto
        updated_cliente = cliente_schema.load(
            request.get_json(),
            instance=cliente,  # Actualiza la instancia existente
            partial=True        # Permite actualizar solo algunos campos
        )
        # Guarda los cambios en la base de datos
        db.session.commit()
        # Serializa y devuelve la respuesta
        return cliente_schema.dump(updated_cliente), 200


    @jwt_required()
    @handle_db_errors
    def delete(self, cliente_id):
        cliente = Cliente.query.get_or_404(cliente_id)
        
        db.session.delete(cliente)
        db.session.commit()
        return "", 204  # 204 No Content
