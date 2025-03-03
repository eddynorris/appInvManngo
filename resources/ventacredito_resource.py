from flask_restful import Resource
from flask_jwt_extended import jwt_required
from flask import request
from models import VentaCredito
from schemas import ventas_credito_schema , venta_credito_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE

class VentaCreditoResource(Resource):
    @jwt_required()
    def get(self, credito_id=None):
        if credito_id:
            credito = VentaCredito.query.get_or_404(credito_id)
            return venta_credito_schema.dump(credito), 200
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        creditos = VentaCredito.query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            "data": venta_credito_schema.dump(creditos.items),
            "pagination": {
                "total": creditos.total,
                "page": creditos.page,
                "per_page": creditos.per_page,
                "pages": creditos.pages            
            }        
        }, 200

    @jwt_required()
    def post(self):
        nuevo_credito = venta_credito_schema.load(request.get_json())
        db.session.add(nuevo_credito)
        db.session.commit()
        return venta_credito_schema.dump(nuevo_credito), 201

    @jwt_required()
    def put(self, credito_id):
        credito = VentaCredito.query.get_or_404(credito_id)
        updated_credito = venta_credito_schema.load(
            request.get_json(),
            instance=credito,
            partial=True
        )
        db.session.commit()
        return venta_credito_schema.dump(updated_credito), 200

    @jwt_required()
    def delete(self, credito_id):
        credito = VentaCredito.query.get_or_404(credito_id)
        db.session.delete(credito)
        db.session.commit()
        return {"message": "Venta a crédito eliminada"}, 204