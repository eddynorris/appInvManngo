from flask_restful import Resource
from flask_jwt_extended import jwt_required
from flask import request
from models import Venta, VentaDetalle, VentaCredito
from schemas import venta_schema, ventas_schema, venta_detalle_schema, venta_credito_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE

class VentaResource(Resource):
    @jwt_required()
    def get(self, venta_id=None):
        if venta_id:
            venta = Venta.query.get_or_404(venta_id)
            return venta_schema.dump(venta), 200
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        ventas = Venta.query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            "data": venta_schema.dump(ventas.items),
            "pagination": {
                "total": ventas.total,
                "page": ventas.page,
                "per_page": ventas.per_page,
                "pages": ventas.pages            
            }        
        }, 200

    @jwt_required()
    def post(self):
        data = request.get_json()
        detalles = data.pop("detalles", [])

        nueva_venta = venta_schema.load(data)
        db.session.add(nueva_venta)
        db.session.commit()


        # Guardar detalles de la venta
        for detalle_data in detalles:
            detalle = venta_detalle_schema.load({
                "venta_id": nueva_venta.id,
                **detalle_data
            })
            db.session.add(detalle)

        # Si es una venta a crédito, guardar los datos de crédito
        if nueva_venta.tipo_pago == "credito":
            credito_data = data.get("credito", {})
            credito = venta_credito_schema.load({
                "venta_id": nueva_venta.id,
                **credito_data
            })
            db.session.add(credito)

        db.session.commit()
        # Reload the venta to get all related data
        venta_completa = Venta.query.get(nueva_venta.id)
        return venta_schema.dump(venta_completa), 201

    @jwt_required()
    def put(self, venta_id):
        venta = Venta.query.get_or_404(venta_id)
        data = request.get_json()
        updated_venta = venta_schema.load(
            data,
            instance=venta,
            partial=True
        )

        # Actualizar detalles de la venta
        if "detalles" in data:
            for detalle_data in data["detalles"]:
                detalle = VentaDetalle.query.filter_by(venta_id=venta_id, producto_id=detalle_data["producto_id"]).first()
                if detalle:
                    venta_detalle_schema.load(detalle_data, instance=detalle, partial=True)
                else:
                    nuevo_detalle = venta_detalle_schema.load({
                        "venta_id": venta_id,
                        **detalle_data
                    })
                    db.session.add(nuevo_detalle)

        # Actualizar datos de crédito si existe
        if venta.tipo_pago == "credito" and "credito" in data:
            credito = venta.credito
            if credito:
                venta_credito_schema.load(data["credito"], instance=credito, partial=True)
            else:
                nuevo_credito = venta_credito_schema.load({
                    "venta_id": venta_id,
                    **data["credito"]
                })
                db.session.add(nuevo_credito)

        db.session.commit()
        return venta_schema.dump(updated_venta), 200

    @jwt_required()
    def delete(self, venta_id):
        venta = Venta.query.get_or_404(venta_id)
        db.session.delete(venta)
        db.session.commit()
        return {"message": "Venta eliminada"}, 204