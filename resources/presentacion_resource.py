from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt
from flask import request
from models import PresentacionProducto, Inventario, VentaDetalle
from schemas import presentacion_schema, presentaciones_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE, rol_requerido

class PresentacionProductoResource(Resource):
    @jwt_required()
    @handle_db_errors
    def get(self, presentacion_id=None):
        """
        Obtiene presentaciones de productos
        - Con ID: Detalle completo con producto asociado
        - Sin ID: Lista paginada con filtros (producto_id, tipo, activo)
        """
        if presentacion_id:
            presentacion = PresentacionProducto.query.get_or_404(presentacion_id)
            return presentacion_schema.dump(presentacion), 200

        # Construir query con filtros
        query = PresentacionProducto.query
        if producto_id := request.args.get('producto_id'):
            query = query.filter_by(producto_id=producto_id)
        if tipo := request.args.get('tipo'):
            query = query.filter_by(tipo=tipo)
        if activo := request.args.get('activo'):
            query = query.filter_by(activo=activo.lower() == 'true')

        # Paginación
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        resultado = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "data": presentaciones_schema.dump(resultado.items),
            "pagination": {
                "total": resultado.total,
                "page": resultado.page,
                "per_page": resultado.per_page,
                "pages": resultado.pages
            }
        }, 200

    @jwt_required()
    @rol_requerido('admin', 'gerente')
    @handle_db_errors
    def post(self):
        """Crea nueva presentación (Requiere rol admin/gerente)"""
        data = presentacion_schema.load(request.get_json())
        nueva_presentacion = PresentacionProducto(**data)
        db.session.add(nueva_presentacion)
        db.session.commit()
        return presentacion_schema.dump(nueva_presentacion), 201

    @jwt_required()
    @rol_requerido('admin', 'gerente')
    @handle_db_errors
    def put(self, presentacion_id):
        """Actualiza presentación existente (Requiere rol admin/gerente)"""
        presentacion = PresentacionProducto.query.get_or_404(presentacion_id)
        data = presentacion_schema.load(request.get_json(), partial=True)

        # Validar campos inmutables
        if 'producto_id' in data and data['producto_id'] != presentacion.producto_id:
            return {"error": "No se puede modificar el producto asociado"}, 400

        for key, value in data.items():
            setattr(presentacion, key, value)

        db.session.commit()
        return presentacion_schema.dump(presentacion), 200

    @jwt_required()
    @rol_requerido('admin')
    @handle_db_errors
    def delete(self, presentacion_id):
        """Elimina presentación (Solo admin) si no tiene registros asociados"""
        presentacion = PresentacionProducto.query.get_or_404(presentacion_id)

        # Verificar dependencias
        if Inventario.query.filter_by(presentacion_id=presentacion_id).first():
            return {"error": "Existen registros de inventario asociados"}, 400
        if VentaDetalle.query.filter_by(presentacion_id=presentacion_id).first():
            return {"error": "Existen ventas asociadas"}, 400

        db.session.delete(presentacion)
        db.session.commit()
        return "", 204