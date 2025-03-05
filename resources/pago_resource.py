# ARCHIVO: pago_resource.py
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt
from flask import request
from models import Pago, Venta
from schemas import pago_schema, pagos_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE
from decimal import Decimal

class PagoResource(Resource):
    @jwt_required()
    @handle_db_errors
    def get(self, pago_id=None):
        """
        Obtiene pagos registrados
        - Con ID: Detalle completo del pago con relación a la venta
        - Sin ID: Lista paginada con filtros (venta_id, método_pago)
        """
        if pago_id:
            return pago_schema.dump(Pago.query.get_or_404(pago_id)), 200
        
        # Construir query con filtros
        query = Pago.query
        if venta_id := request.args.get('venta_id'):
            query = query.filter_by(venta_id=venta_id)
        if metodo := request.args.get('metodo_pago'):
            query = query.filter_by(metodo_pago=metodo)

        # Paginación
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        resultado = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            "data": pagos_schema.dump(resultado.items),
            "pagination": resultado.pagination
        }, 200

    @jwt_required()
    @handle_db_errors
    def post(self):
        """Registra nuevo pago y actualiza estado de la venta"""
        data = pago_schema.load(request.get_json())
        venta = Venta.query.get_or_404(data['venta_id'])
        
        # Validar que el pago no exceda el saldo pendiente
        if Decimal(data['monto']) > venta.saldo_pendiente:
            return {"error": "Monto excede el saldo pendiente"}, 400
        
        nuevo_pago = Pago(**data)
        db.session.add(nuevo_pago)
        
        # Actualizar estado de la venta
        venta.actualizar_estado()
        db.session.commit()
        
        return pago_schema.dump(nuevo_pago), 201

    @jwt_required()
    @handle_db_errors
    def put(self, pago_id):
        """Actualiza pago existente y recalcula estado de venta"""
        pago = Pago.query.get_or_404(pago_id)
        data = pago_schema.load(request.get_json(), partial=True)
        
        # Validar monto si se modifica
        if 'monto' in data:
            diferencia = data['monto'] - pago.monto
            if diferencia > pago.venta.saldo_pendiente + pago.monto:
                return {"error": "Nuevo monto excede saldo pendiente"}, 400
            
        for key, value in data.items():
            setattr(pago, key, value)
        
        pago.venta.actualizar_estado()
        db.session.commit()
        return pago_schema.dump(pago), 200

    @jwt_required()
    @handle_db_errors
    def delete(self, pago_id):
        """Elimina pago y actualiza estado de la venta relacionada"""
        pago = Pago.query.get_or_404(pago_id)
        venta = pago.venta
        
        db.session.delete(pago)
        venta.actualizar_estado()
        db.session.commit()
        return "", 204