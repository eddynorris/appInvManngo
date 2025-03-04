from flask_restful import Resource
from flask_jwt_extended import jwt_required
from flask import request
from models import Pago, Venta
from schemas import pago_schema, pagos_schema  # Asegúrate de tener estos esquemas
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE
from decimal import Decimal

class PagoResource(Resource):
    @jwt_required()
    @handle_db_errors
    def get(self, pago_id=None):
        if pago_id:
            # Obtener un pago específico
            pago = Pago.query.get_or_404(pago_id)
            return pago_schema.dump(pago), 200
        
        # Paginación para listar todos los pagos
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        pagos = Pago.query.paginate(page=page, per_page=per_page, error_out=False)
        
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
        data = request.get_json()
        venta_id = data.get("venta_id")
        
        # Validar que la venta existe y es a crédito
        venta = Venta.query.get_or_404(venta_id)
        if venta.tipo_pago != "credito":
            return {"error": "Solo se pueden agregar pagos a ventas a crédito"}, 400
        
        # Validar que el monto no exceda el saldo
        monto = Decimal(data["monto"])
        if monto > venta.saldo_pendiente:
            return {"error": "El monto excede el saldo pendiente"}, 400
        
        # Crear y guardar el pago
        nuevo_pago = pago_schema.load(data)
        db.session.add(nuevo_pago)
        
        # Actualizar estado de la venta
        venta.actualizar_estado()  # Método del modelo Venta para actualizar estado_pago
        db.session.commit()
        
        return pago_schema.dump(nuevo_pago), 201

    @jwt_required()
    @handle_db_errors
    def put(self, pago_id):
        pago = Pago.query.get_or_404(pago_id)
        data = request.get_json()
        
        # Validar monto si se actualiza
        if "monto" in data:
            venta = pago.venta
            nuevo_monto = Decimal(data["monto"])
            diferencia = nuevo_monto - pago.monto
            
            if (venta.saldo_pendiente + pago.monto) < nuevo_monto:  # Saldo previo + monto antiguo
                return {"error": "El monto excede el saldo pendiente"}, 400
            
            pago.monto = nuevo_monto
        
        # Actualizar otros campos
        pago_actualizado = pago_schema.load(
            data,
            instance=pago,
            partial=True
        )
        
        # Actualizar estado de la venta
        pago_actualizado.venta.actualizar_estado()
        db.session.commit()
        
        return pago_schema.dump(pago_actualizado), 200

    @jwt_required()
    @handle_db_errors
    def delete(self, pago_id):
        pago = Pago.query.get_or_404(pago_id)
        venta = pago.venta
        
        db.session.delete(pago)
        venta.actualizar_estado()  # Actualizar estado después de eliminar
        db.session.commit()
        
        return {"message": "Pago eliminado correctamente"}, 204