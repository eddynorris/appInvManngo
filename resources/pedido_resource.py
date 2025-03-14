from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt
from flask import request
from models import Pedido, PedidoDetalle, Cliente, PresentacionProducto, Almacen, Inventario, Movimiento
from schemas import pedido_schema, pedidos_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE, mismo_almacen_o_admin
from datetime import datetime, timezone

class PedidoResource(Resource):
    @jwt_required()
    @handle_db_errors
    def get(self, pedido_id=None):
        """
        Obtiene pedido(s)
        - Con ID: Detalle completo del pedido
        - Sin ID: Lista paginada con filtros (cliente_id, almacen_id, fecha_inicio, fecha_fin, estado)
        """
        if pedido_id:
            pedido = Pedido.query.get_or_404(pedido_id)
            return pedido_schema.dump(pedido), 200
        
        # Construir query con filtros
        query = Pedido.query
        
        # Aplicar filtros
        if cliente_id := request.args.get('cliente_id'):
            query = query.filter_by(cliente_id=cliente_id)
        
        if almacen_id := request.args.get('almacen_id'):
            query = query.filter_by(almacen_id=almacen_id)
        
        if vendedor_id := request.args.get('vendedor_id'):
            query = query.filter_by(vendedor_id=vendedor_id)
            
        if estado := request.args.get('estado'):
            query = query.filter_by(estado=estado)
            
        if fecha_inicio := request.args.get('fecha_inicio'):
            if fecha_fin := request.args.get('fecha_fin'):
                try:
                    fecha_inicio = datetime.fromisoformat(fecha_inicio).replace(tzinfo=timezone.utc)
                    fecha_fin = datetime.fromisoformat(fecha_fin).replace(tzinfo=timezone.utc)
                    
                    # Filtrar por fecha de entrega
                    query = query.filter(Pedido.fecha_entrega.between(fecha_inicio, fecha_fin))
                except ValueError:
                    return {"error": "Formato de fecha inválido. Usa ISO 8601 (ej: '2025-03-05T00:00:00')"}, 400
        
        # Paginación
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        pedidos = query.paginate(page=page, per_page=per_page)
        
        return {
            "data": pedidos_schema.dump(pedidos.items),
            "pagination": {
                "total": pedidos.total,
                "page": pedidos.page,
                "per_page": pedidos.per_page,
                "pages": pedidos.pages
            }
        }, 200

    @jwt_required()
    @mismo_almacen_o_admin
    @handle_db_errors
    def post(self):
        """
        Crea un nuevo pedido programado
        """
        data = pedido_schema.load(request.get_json())
        
        # Validaciones
        Cliente.query.get_or_404(data.cliente_id)
        Almacen.query.get_or_404(data.almacen_id)
        
        # Asignar vendedor automáticamente desde JWT
        claims = get_jwt()
        data.vendedor_id = claims.get('sub')
        
        # Validar detalles del pedido
        for detalle in data.detalles:
            presentacion = PresentacionProducto.query.get_or_404(detalle.presentacion_id)
            # El precio estimado usualmente es el de venta actual, pero podría ser diferente
            if not detalle.precio_estimado:
                detalle.precio_estimado = presentacion.precio_venta
        
        db.session.add(data)
        db.session.commit()
        
        return pedido_schema.dump(data), 201

    @jwt_required()
    @mismo_almacen_o_admin
    @handle_db_errors
    def put(self, pedido_id):
        """
        Actualiza un pedido existente
        """
        pedido = Pedido.query.get_or_404(pedido_id)
        
        # Validar estados - no permitir actualizar pedidos entregados
        if pedido.estado == 'entregado':
            return {"error": "No se puede modificar un pedido ya entregado"}, 400
        
        updated_pedido = pedido_schema.load(
            request.get_json(),
            instance=pedido,
            partial=True
        )
        
        db.session.commit()
        return pedido_schema.dump(updated_pedido), 200
    
    @jwt_required()
    @mismo_almacen_o_admin
    @handle_db_errors
    def delete(self, pedido_id):
        """
        Elimina un pedido (o lo marca como cancelado)
        """
        pedido = Pedido.query.get_or_404(pedido_id)
        
        # Si ya está entregado, no permite eliminar
        if pedido.estado == 'entregado':
            return {"error": "No se puede eliminar un pedido ya entregado"}, 400
        
        # Opción 1: Eliminar
        db.session.delete(pedido)
        
        # Opción 2: Marcar como cancelado (alternativa)
        # pedido.estado = 'cancelado'
        
        db.session.commit()
        return "Pedido eliminado correctamente", 200

class PedidoConversionResource(Resource):
    @jwt_required()
    @mismo_almacen_o_admin
    @handle_db_errors
    def post(self, pedido_id):
        """
        Convierte un pedido en una venta real
        """
        from models import Venta, VentaDetalle
        from schemas import venta_schema
        
        pedido = Pedido.query.get_or_404(pedido_id)
        
        # Validar que no esté ya entregado
        if pedido.estado == 'entregado':
            return {"error": "Este pedido ya fue entregado"}, 400
        
        # Verificar stock antes de proceder
        for detalle in pedido.detalles:
            inventario = Inventario.query.filter_by(
                presentacion_id=detalle.presentacion_id,
                almacen_id=pedido.almacen_id
            ).first()
            
            if not inventario or inventario.cantidad < detalle.cantidad:
                return {
                    "error": f"Stock insuficiente para {detalle.presentacion.nombre}",
                    "stock_disponible": inventario.cantidad if inventario else 0
                }, 400
        
        # Crear venta desde pedido
        venta = Venta(
            cliente_id=pedido.cliente_id,
            almacen_id=pedido.almacen_id,
            tipo_pago='contado',  # Valor predeterminado, puede modificarse
            estado_pago='pendiente'
        )
        
        # Agregar detalles
        total = 0
        for detalle_pedido in pedido.detalles:
            detalle_venta = VentaDetalle(
                presentacion_id=detalle_pedido.presentacion_id,
                cantidad=detalle_pedido.cantidad,
                precio_unitario=detalle_pedido.precio_estimado
            )
            venta.detalles.append(detalle_venta)
            total += detalle_venta.cantidad * detalle_venta.precio_unitario
        
        venta.total = total
        
        # Actualizar inventario y crear movimientos
        claims = get_jwt()
        for detalle in venta.detalles:
            inventario = Inventario.query.filter_by(
                presentacion_id=detalle.presentacion_id,
                almacen_id=venta.almacen_id
            ).first()
            
            inventario.cantidad -= detalle.cantidad
            
            movimiento = Movimiento(
                tipo='salida',
                presentacion_id=detalle.presentacion_id,
                lote_id=inventario.lote_id,
                cantidad=detalle.cantidad,
                usuario_id=claims['sub'],
                motivo=f"Venta ID: {venta.id} - Cliente: {pedido.cliente.nombre} (desde pedido {pedido.id})"
            )
            db.session.add(movimiento)
        
        # Marcar pedido como entregado
        pedido.estado = 'entregado'
        
        db.session.add(venta)
        db.session.commit()
        
        return {
            "message": "Pedido convertido a venta exitosamente",
            "venta": venta_schema.dump(venta)
        }, 201