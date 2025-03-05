from flask_restful import Resource
from flask_jwt_extended import jwt_required
from flask import request
from models import Producto, PresentacionProducto
from schemas import producto_schema, productos_schema, presentacion_schema, presentaciones_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE

class ProductoResource(Resource):
    @jwt_required()
    @handle_db_errors
    def get(self, producto_id=None):
        if producto_id:
            producto = Producto.query.get_or_404(producto_id)
            return producto_schema.dump(producto), 200
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        productos = Producto.query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            "data": productos_schema.dump(productos.items),
            "pagination": {
                "total": productos.total,
                "page": productos.page,
                "per_page": productos.per_page,
                "pages": productos.pages
            }
        }, 200

    @jwt_required()
    @handle_db_errors
    def post(self):
        data = producto_schema.load(request.get_json())
        db.session.add(data)
        db.session.commit()
        return producto_schema.dump(data), 201

    @jwt_required()
    @handle_db_errors
    def put(self, producto_id):
        producto = Producto.query.get_or_404(producto_id)
        updated_producto = producto_schema.load(
            request.get_json(),
            instance=producto,
            partial=True
        )
        db.session.commit()
        return producto_schema.dump(updated_producto), 200

    @jwt_required()
    @handle_db_errors
    def delete(self, producto_id):
        producto = Producto.query.get_or_404(producto_id)
        db.session.delete(producto)
        db.session.commit()
        return "", 204

# --- Nuevo recurso para PresentacionesProducto ---
class PresentacionProductoResource(Resource):
    @jwt_required()
    @handle_db_errors
    def post(self):
        data = presentacion_schema.load(request.get_json())
        db.session.add(data)
        db.session.commit()
        return presentacion_schema.dump(data), 201

    @jwt_required()
    @handle_db_errors
    def get(self, presentacion_id=None):
        if presentacion_id:
            presentacion = PresentacionProducto.query.get_or_404(presentacion_id)
            return presentacion_schema.dump(presentacion), 200
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        presentaciones = PresentacionProducto.query.paginate(page=page, per_page=per_page)
        
        return {
            "data": presentaciones_schema.dump(presentaciones.items),
            "pagination": {
                "total": presentaciones.total,
                "page": presentaciones.page,
                "per_page": presentaciones.per_page,
                "pages": presentaciones.pages
            }
        }, 200