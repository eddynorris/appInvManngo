# ARCHIVO: gasto_resource.py
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt
from flask import request
from models import Gasto
from schemas import gasto_schema, gastos_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE

class GastoResource(Resource):
    @jwt_required()
    @handle_db_errors
    def get(self, gasto_id=None):
        """
        Obtiene registros de gastos
        - Con ID: Detalle completo con relaciones
        - Sin ID: Lista paginada con filtros (categoría, fecha)
        """
        if gasto_id:
            return gasto_schema.dump(Gasto.query.get_or_404(gasto_id)), 200
        
        # Construir query con filtros
        query = Gasto.query
        if categoria := request.args.get('categoria'):
            query = query.filter_by(categoria=categoria)
        if fecha := request.args.get('fecha'):
            query = query.filter_by(fecha=fecha)

        # Paginación
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        resultado = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            "data": gastos_schema.dump(resultado.items),
            "pagination": resultado.pagination
        }, 200

    @jwt_required()
    @handle_db_errors
    def post(self):
        """Registra nuevo gasto con validación de categoría"""
        data = gasto_schema.load(request.get_json())
        data['usuario_id'] = get_jwt().get('sub')  # Asignar usuario actual
        
        nuevo_gasto = Gasto(**data)
        db.session.add(nuevo_gasto)
        db.session.commit()
        return gasto_schema.dump(nuevo_gasto), 201

    @jwt_required()
    @handle_db_errors
    def put(self, gasto_id):
        """Actualiza gasto existente con validación de datos"""
        gasto = Gasto.query.get_or_404(gasto_id)
        data = gasto_schema.load(request.get_json(), partial=True)
        
        # Campos no modificables
        if 'usuario_id' in data:
            return {"error": "No se puede modificar el usuario del gasto"}, 400
        
        for key, value in data.items():
            setattr(gasto, key, value)
        
        db.session.commit()
        return gasto_schema.dump(gasto), 200

    @jwt_required()
    @handle_db_errors
    def delete(self, gasto_id):
        """Elimina registro de gasto"""
        gasto = Gasto.query.get_or_404(gasto_id)
        db.session.delete(gasto)
        db.session.commit()
        return "", 204