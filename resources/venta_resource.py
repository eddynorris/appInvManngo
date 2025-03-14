from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt
from flask import request
from models import Venta, VentaDetalle, Inventario, Cliente, PresentacionProducto, Almacen, Movimiento
from schemas import venta_schema, ventas_schema, venta_detalle_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE, mismo_almacen_o_admin
from datetime import datetime, timezone
from decimal import Decimal

class VentaResource(Resource):
    @jwt_required()
    @handle_db_errors
    def get(self, venta_id=None):
        if venta_id:
            venta = Venta.query.get_or_404(venta_id)
            return venta_schema.dump(venta), 200
        
        # Filtros: cliente_id, almacen_id, fecha_inicio, fecha_fin
        filters = {
            "cliente_id": request.args.get('cliente_id'),
            "almacen_id": request.args.get('almacen_id'),
            "fecha_inicio": request.args.get('fecha_inicio'),
            "fecha_fin": request.args.get('fecha_fin')
        }
        
        query = Venta.query
        
        # Aplicar filtros
        if filters["cliente_id"]:
            query = query.filter_by(cliente_id=filters["cliente_id"])
        if filters["almacen_id"]:
            query = query.filter_by(almacen_id=filters["almacen_id"])
        if filters["fecha_inicio"] and filters["fecha_fin"]:
            try:
                # Asegurando formato ISO y manejar zonas horarias
                fecha_inicio = datetime.fromisoformat(filters["fecha_inicio"]).replace(tzinfo=timezone.utc)
                fecha_fin = datetime.fromisoformat(filters["fecha_fin"]).replace(tzinfo=timezone.utc)
                query = query.filter(Venta.fecha.between(fecha_inicio, fecha_fin))
            except ValueError as e:
                # Manejar error de formato inválido
                return {"error": "Formato de fecha inválido. Usa ISO 8601 (ej: '2025-03-05T00:00:00')"}, 400
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        ventas = query.paginate(page=page, per_page=per_page)
        
        return {
            "data": ventas_schema.dump(ventas.items),
            "pagination": {
                "total": ventas.total,
                "page": ventas.page,
                "per_page": ventas.per_page,
                "pages": ventas.pages
            }
        }, 200


    @jwt_required()
    @mismo_almacen_o_admin
    @handle_db_errors
    def post(self):
        data = venta_schema.load(request.get_json())

        cliente = Cliente.query.get_or_404(data.cliente_id)
        almacen = Almacen.query.get_or_404(data.almacen_id)

        total = Decimal('0')
        inventarios_a_actualizar = {}
        movimientos = []  # Lista para almacenar los movimientos
        claims = get_jwt()

        for detalle in data.detalles:
            presentacion = PresentacionProducto.query.get_or_404(detalle.presentacion_id)

            inventario = Inventario.query.filter_by(
                presentacion_id=presentacion.id,
                almacen_id=data.almacen_id
            ).first()

            if not inventario or inventario.cantidad < detalle.cantidad:
                return {"error": f"Stock insuficiente para {presentacion.nombre}"}, 400
            if not detalle.precio_unitario:
                detalle.precio_unitario = presentacion.precio_venta

            if not inventario:
                return {"error": f"La presentación {presentacion.nombre} no está disponible en este almacén"}, 400
    
            if inventario.cantidad < detalle.cantidad:
              return {"error": f"Stock insuficiente para {presentacion.nombre} (Disponible: {inventario.cantidad})"}, 400

            # Asignar precio unitario si no viene
            if not hasattr(detalle, 'precio_unitario') or not detalle.precio_unitario:
                detalle.precio_unitario = presentacion.precio_venta
            # Registrar datos para el movimiento
            movimientos.append({
                "presentacion_id": presentacion.id,
                "lote_id": inventario.lote_id,  # Obtenemos el lote del inventario
                "cantidad": detalle.cantidad
            })

            total += detalle.cantidad * detalle.precio_unitario
            inventarios_a_actualizar[presentacion.id] = (inventario, detalle.cantidad)

        nueva_venta = Venta(
            cliente_id=data.cliente_id,
            almacen_id=data.almacen_id,
            total=total,
            tipo_pago=data.tipo_pago,
            consumo_diario_kg=data.consumo_diario_kg,
            detalles=data.detalles
        )

        try:
            db.session.add(nueva_venta)
            db.session.flush()  # Generamos el ID de la venta

            # Crear movimientos después de obtener el ID de la venta
            for movimiento_data in movimientos:
                movimiento = Movimiento(
                    tipo='salida',
                    presentacion_id=movimiento_data["presentacion_id"],
                    lote_id=movimiento_data["lote_id"],
                    cantidad=movimiento_data["cantidad"],
                    usuario_id=claims['sub'],
                    motivo=f"Venta ID: {nueva_venta.id} - Cliente: {cliente.nombre}"
                )
                db.session.add(movimiento)

            # Actualizar inventarios
            for inventario, cantidad in inventarios_a_actualizar.values():
                inventario.cantidad -= cantidad

            # Actualizar proyección del cliente
            if nueva_venta.consumo_diario_kg:
                if Decimal(nueva_venta.consumo_diario_kg) <= 0:
                    raise ValueError("El consumo diario debe ser mayor a 0")

                cliente.ultima_fecha_compra = datetime.utcnow()
                cliente.frecuencia_compra_dias = (total / Decimal(nueva_venta.consumo_diario_kg)).quantize(Decimal('1.00'))

            db.session.commit()
            return venta_schema.dump(nueva_venta), 201

        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    @jwt_required()
    @mismo_almacen_o_admin
    @handle_db_errors
    def put(self, venta_id):
        venta = Venta.query.get_or_404(venta_id)
        raw_data = request.get_json()
        

        # Validar campos inmutables
        immutable_fields = ["detalles", "almacen_id"]
        for field in immutable_fields:
            if field in raw_data and str(raw_data[field]) != str(getattr(venta, field)):
                return {"error": f"Campo inmutable '{field}' no puede modificarse"}, 400
                # Cargar datos validados sobre la instancia existente

        updated_venta = venta_schema.load(
            raw_data,
            instance=venta,
            partial=True
        )

        db.session.commit()
        return venta_schema.dump(updated_venta), 200

    @jwt_required()
    @mismo_almacen_o_admin
    @handle_db_errors
    def delete(self, venta_id):
        venta = Venta.query.get_or_404(venta_id)
        
        try:
            # Revertir movimientos e inventario
            movimientos = Movimiento.query.filter(
                Movimiento.motivo.like(f"Venta ID: {venta_id}%")
            ).all()
            
            for movimiento in movimientos:
                inventario = Inventario.query.filter_by(
                    presentacion_id=movimiento.presentacion_id,
                    almacen_id=venta.almacen_id
                ).first()
                
                if inventario:
                    inventario.cantidad += movimiento.cantidad
                
                db.session.delete(movimiento)
            
            db.session.delete(venta)
            db.session.commit()
            
            return {"message": "Venta eliminada con éxito"}, 200
            
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500
    