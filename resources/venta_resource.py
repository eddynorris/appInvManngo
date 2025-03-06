from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt
from flask import request
from models import Venta, VentaDetalle, Inventario, Cliente, PresentacionProducto, Almacen
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
        almacen_id = data["almacen_id"]
        
        # Validar cliente y almacén
        cliente = Cliente.query.get_or_404(data["cliente_id"])
        almacen = Almacen.query.get_or_404(almacen_id)
        
        total = Decimal('0')
        detalles = []
        inventarios_a_actualizar = {}
    
        # Procesar y validar cada detalle de venta
        for detalle_data in data["detalles"]:
            presentacion = PresentacionProducto.query.get_or_404(detalle_data["presentacion_id"])
            
            # Verificar stock en inventario
            inventario = Inventario.query.filter_by(
                presentacion_id=presentacion.id,
                almacen_id=almacen_id
            ).first()
            
            cantidad = detalle_data["cantidad"]
            
            if not inventario or inventario.cantidad < cantidad:
                return {
                    "error": f"Stock insuficiente para {presentacion.nombre}",
                    "presentacion_id": presentacion.id,
                    "stock_disponible": inventario.cantidad if inventario else 0
                }, 400
            
            # Calcular subtotal usando el modelo
            detalle = VentaDetalle(
                presentacion_id=presentacion.id,
                cantidad=cantidad,
                precio_unitario=presentacion.precio_venta
            )
            
            total += detalle.total_linea
            detalles.append(detalle)
            inventarios_a_actualizar[presentacion.id] = (inventario, cantidad)
    
        # Crear venta
        nueva_venta = Venta(
            cliente_id=cliente.id,
            almacen_id=almacen_id,
            total=total,
            tipo_pago=data["tipo_pago"],
            consumo_diario_kg=data.get("consumo_diario_kg"),
            detalles=detalles
        )
    
        try:
            # Actualizar stock y proyección de cliente
            for inventario, cantidad in inventarios_a_actualizar.values():
                inventario.cantidad -= cantidad
            
            if nueva_venta.consumo_diario_kg:
                if Decimal(nueva_venta.consumo_diario_kg) <= 0:
                    raise ValueError("El consumo diario debe ser mayor a 0")
                
                cliente.ultima_fecha_compra = datetime.utcnow()
                cliente.frecuencia_compra_dias = (total / Decimal(nueva_venta.consumo_diario_kg)).quantize(Decimal('1.'))
            
            db.session.add(nueva_venta)
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
        data = venta_schema.load(request.get_json(), partial=True)
        
        # Campos inmutables
        if "almacen_id" in data and data["almacen_id"] != venta.almacen_id:
            return {"error": "No se puede modificar el almacén de una venta"}, 400
        
        # Actualizar campos permitidos (ej: estado_pago, consumo_diario_kg)
        for key, value in data.items():
            if key in ["estado_pago", "consumo_diario_kg", "tipo_pago"]:
                setattr(venta, key, value)
        
        venta.actualizar_estado()  # Método del modelo para recalcular estado_pago
        db.session.commit()
        
        return venta_schema.dump(venta), 200

    @jwt_required()
    @mismo_almacen_o_admin
    @handle_db_errors
    def delete(self, venta_id):
        venta = Venta.query.get_or_404(venta_id)
        
        # Revertir stock
        for detalle in venta.detalles:
            inventario = Inventario.query.filter_by(
                presentacion_id=detalle.presentacion_id,
                almacen_id=venta.almacen_id
            ).first()
            inventario.cantidad += detalle.cantidad
        
        db.session.delete(venta)
        db.session.commit()
        
        return "", 204
