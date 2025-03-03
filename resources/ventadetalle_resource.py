from flask_restful import Resource
from flask_jwt_extended import jwt_required
from flask import request
from models import VentaDetalle
from schemas import venta_detalle_schema , ventas_detalle_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE


class VentaDetalleResource(Resource):
    @jwt_required()
    @handle_db_errors
    def get(self, detalle_id=None):
        if detalle_id:
            detalle = VentaDetalle.query.get_or_404(detalle_id)
            return venta_detalle_schema.dump(detalle), 200
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        detalles = VentaDetalle.query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            "data": venta_detalle_schema.dump(detalles.items),
            "pagination": {
                "total": detalles.total,
                "page": detalles.page,
                "per_page": detalles.per_page,
                "pages": detalles.pages            
            }        
        }, 200        

    @jwt_required()
    @handle_db_errors
    def post(self):
        nuevo_detalle = venta_detalle_schema.load(request.get_json())
        db.session.add(nuevo_detalle)
        db.session.commit()
        return venta_detalle_schema.dump(nuevo_detalle), 201


    @jwt_required()
    @handle_db_errors
    def put(self, detalle_id):
        detalle = VentaDetalle.query.get_or_404(detalle_id)
        updated_detalle = venta_detalle_schema.load(
            request.get_json(),
            instance=detalle,
            partial=True
        )
        db.session.commit()
        return venta_detalle_schema.dump(updated_detalle), 200

    @jwt_required()
    @handle_db_errors
    def delete(self, detalle_id):
        detalle = VentaDetalle.query.get_or_404(detalle_id)
        db.session.delete(detalle)
        db.session.commit()
        return {"message": "Detalle de venta eliminado"}, 204