from flask_restful import Resource
from flask_jwt_extended import jwt_required
from flask import request
from models import Producto
from schemas import producto_schema, productos_schema
from extensions import db
from decimal import Decimal
from common import handle_db_errors, MAX_ITEMS_PER_PAGE

class ProductoResource(Resource):
    @jwt_required()
    def get(self, producto_id=None):
        if producto_id:
            producto = Producto.query.get_or_404(producto_id)
            return producto_schema.dump(producto), 200
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        productos = Producto.query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "data": producto_schema.dump(productos.items),
            "pagination": {
                "total": productos.total,
                "page": productos.page,
                "per_page": productos.per_page,
                "pages": productos.pages            
            }
        }, 200

    @jwt_required()
    def post(self):
       
        nuevo_producto = producto_schema.load(request.get_json())
        db.session.add(nuevo_producto)
        db.session.commit()
        return producto_schema.dump(nuevo_producto), 201

    @jwt_required()
    def put(self, producto_id):
        # Obtiene el producto existente de la base de datos
        producto = Producto.query.get_or_404(producto_id)
        
        # Deserializa los datos recibidos y actualiza la instancia del producto
        updated_producto = producto_schema.load(
            request.get_json(),
            instance=producto,  # Actualiza la instancia existente
            partial=True        # Permite actualizar solo algunos campos
        )
        
        # Guarda los cambios en la base de datos
        db.session.commit()
        
        # Serializa y devuelve la respuesta
        return producto_schema.dump(updated_producto), 200
 
    @jwt_required()
    def delete(self, producto_id):
        producto = Producto.query.get_or_404(producto_id)
        db.session.delete(producto)
        db.session.commit()
        return {"message": "Producto eliminado"}, 204