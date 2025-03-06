# ARCHIVO: cliente_resource.py
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from flask import request
from models import Cliente
from schemas import cliente_schema, clientes_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE

class ClienteResource(Resource):
    @jwt_required()
    @handle_db_errors
    def get(self, cliente_id=None):
        """
        Obtiene cliente(s)
        - Con ID: Detalle completo con saldo pendiente
        - Sin ID: Lista paginada con filtros (nombre, teléfono)
        """
        if cliente_id:
            return cliente_schema.dump(Cliente.query.get_or_404(cliente_id)), 200
        
        # Construir query con filtros
        query = Cliente.query
        if nombre := request.args.get('nombre'):
            query = query.filter(Cliente.nombre.ilike(f'%{nombre}%'))
        if telefono := request.args.get('telefono'):
            query = query.filter(Cliente.telefono == telefono)

        # Paginación
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        resultado = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            "data": clientes_schema.dump(resultado.items),
            "pagination": {
                "total": resultado.total,
                "page": resultado.page,
                "per_page": resultado.per_page,
                "pages": resultado.pages
            }
        }, 200

    @jwt_required()
    @handle_db_errors
    def post(self):
        """Crea nuevo cliente con validación de datos"""
        nuevo_cliente = cliente_schema.load(request.get_json())
        db.session.add(nuevo_cliente)
        db.session.commit()
        return cliente_schema.dump(nuevo_cliente), 201

    @jwt_required()
    @handle_db_errors
    def put(self, cliente_id):
        """Actualiza cliente existente con validación parcial"""
        cliente = Cliente.query.get_or_404(cliente_id)
        cliente_actualizado = cliente_schema.load(
            request.get_json(),
            instance=cliente,
            partial=True
        )
        db.session.commit()
        return cliente_schema.dump(cliente_actualizado), 200

    @jwt_required()
    @handle_db_errors
    def delete(self, cliente_id):
        """Elimina cliente solo si no tiene ventas asociadas"""
        cliente = Cliente.query.get_or_404(cliente_id)
        
        if cliente.ventas:
            return {"error": "No se puede eliminar cliente con historial de ventas"}, 400
            
        db.session.delete(cliente)
        db.session.commit()
        return "Producto eliminado exitosamente", 200