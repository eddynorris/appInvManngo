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
        pagos = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            "data": pagos_schema.dump(pagos.items),
            "pagination": {
                "total": pagos.total,
                "page": pagos.page,
                "per_page": pagos.per_page,
                "pages": pagos.pages
            }
        }, 200

    @jwt_required()
    @handle_db_errors
    def post(self):
        """Registra nuevo pago y actualiza estado de la venta"""
        data = pago_schema.load(request.get_json())
        
        venta = Venta.query.get_or_404(data.venta_id)

        saldo_pendiente_venta = venta.total - sum(pago.monto for pago in venta.pagos)

        if Decimal(data.monto) > saldo_pendiente_venta:
            return {"error": "Monto excede el saldo pendiente"}, 400
        
        nuevo_pago = Pago(
        venta_id=venta.id,
        monto=data.monto,
        metodo_pago=data.metodo_pago,
        referencia=data.referencia,
        usuario_id=get_jwt().get('sub')
        )

        db.session.add(nuevo_pago)
        
        venta.actualizar_estado()
        db.session.commit()
        
        return pago_schema.dump(nuevo_pago), 201

    @jwt_required()
    @handle_db_errors
    def put(self, pago_id):
        pago = Pago.query.get_or_404(pago_id)
        data = pago_schema.load(request.get_json(), partial=True)
        venta = pago.venta
        
        if data.monto:
            nuevo_monto = Decimal(data.monto)
            saldo_actual = venta.total - sum(p.monto for p in venta.pagos if p.id != pago_id)
            
            if nuevo_monto > saldo_actual:
                return {"error": "Nuevo monto excede saldo pendiente"}, 400
            
        updated_pago = pago_schema.load(
            request.get_json(),
            instance=pago,
            partial=True
        )
        venta.actualizar_estado()
        db.session.commit()
        
        return pago_schema.dump(updated_pago), 200
    @jwt_required()
    @handle_db_errors
    def delete(self, pago_id):
        """Elimina pago y actualiza estado de la venta relacionada"""
        pago = Pago.query.get_or_404(pago_id)
        venta = pago.venta
        
        db.session.delete(pago)
        venta.actualizar_estado()
        db.session.commit()
        return "Pago eliminado", 200