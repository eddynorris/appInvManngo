# ARCHIVO: movimiento_resource.py
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt
from flask import request
from models import Movimiento, Inventario
from schemas import movimiento_schema, movimientos_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE

class MovimientoResource(Resource):
    @jwt_required()
    @handle_db_errors
    def get(self, movimiento_id=None):
        """
        Obtiene movimientos de inventario
        - Con ID: Detalle completo con relaciones
        - Sin ID: Lista paginada con filtros (tipo, producto_id)
        """
        if movimiento_id:
            return movimiento_schema.dump(Movimiento.query.get_or_404(movimiento_id)), 200
        
        # Construir query con filtros
        query = Movimiento.query
        if tipo := request.args.get('tipo'):
            query = query.filter_by(tipo=tipo)
        if producto_id := request.args.get('producto_id'):
            query = query.filter_by(producto_id=producto_id)

        # Paginación
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        movimientos = query.paginate(page=page, per_page=per_page, error_out=False)
        
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
        """Registra movimiento y actualiza inventario correspondiente"""
        data = movimiento_schema.load(request.get_json())
        inventario = Inventario.query.filter_by(
            producto_id=data['producto_id'],
            almacen_id=data['almacen_id']
        ).first()
        
        # Validar stock para movimientos de salida
        if data['tipo'] == 'salida' and (not inventario or inventario.cantidad < data['cantidad']):
            return {"error": "Stock insuficiente para este movimiento"}, 400
        
        nuevo_movimiento = Movimiento(**data)
        db.session.add(nuevo_movimiento)
        
        # Actualizar inventario
        if data['tipo'] == 'entrada':
            inventario.cantidad += data['cantidad']
        else:
            inventario.cantidad -= data['cantidad']
        
        db.session.commit()
        return movimiento_schema.dump(nuevo_movimiento), 201

    @jwt_required()
    @handle_db_errors
    def delete(self, movimiento_id):
        """Elimina movimiento y revierte el inventario"""
        movimiento = Movimiento.query.get_or_404(movimiento_id)
        inventario = Inventario.query.filter_by(
            producto_id=movimiento.producto_id,
            almacen_id=movimiento.almacen_id
        ).first()
        
        # Revertir movimiento
        if movimiento.tipo == 'entrada':
            inventario.cantidad -= movimiento.cantidad
        else:
            inventario.cantidad += movimiento.cantidad
        
        db.session.delete(movimiento)
        db.session.commit()
        return "", 204