from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt
from flask import request
from models import Merma, Lote, Inventario, PresentacionProducto
from schemas import merma_schema, mermas_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE

class MermaResource(Resource):
    @jwt_required()
    @handle_db_errors
    def get(self, merma_id=None):
        if merma_id:
            merma = Merma.query.get_or_404(merma_id)
            return merma_schema.dump(merma), 200
        
        # Filtros: lote_id, convertido_a_briquetas, fecha_registro
        lote_id = request.args.get('lote_id')
        convertido = request.args.get('convertido_a_briquetas', type=bool)
        
        query = Merma.query
        
        if lote_id:
            query = query.filter_by(lote_id=lote_id)
        if convertido is not None:
            query = query.filter_by(convertido_a_briquetas=convertido)
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        mermas = query.paginate(page=page, per_page=per_page)
        
        return {
            "data": mermas_schema.dump(mermas.items),
            "pagination": {
                "total": mermas.total,
                "page": mermas.page,
                "per_page": mermas.per_page,
                "pages": mermas.pages
            }
        }, 200

    @jwt_required()
    @handle_db_errors
    def post(self):
        data = merma_schema.load(request.get_json())
        lote = Lote.query.get_or_404(data["lote_id"])
        
        # Validar que la merma no exceda el peso seco del lote
        if data["cantidad_kg"] > lote.peso_seco_kg:
            return {"error": "La merma supera el peso seco del lote"}, 400
        
        # Crear merma
        nueva_merma = Merma(**data)
        db.session.add(nueva_merma)
        
        # Si se convierte a briquetas, actualizar inventario
        if data.get("convertido_a_briquetas"):
            presentacion_briquetas = PresentacionProducto.query.filter_by(
                tipo="briqueta"
            ).first()
            
            if not presentacion_briquetas:
                return {"error": "No existe una presentación para briquetas"}, 400
            
            inventario = Inventario.query.filter_by(
                presentacion_id=presentacion_briquetas.id,
                almacen_id=lote.almacen_id  # Asume que el lote está asociado a un almacén
            ).first()
            
            if not inventario:
                inventario = Inventario(
                    presentacion_id=presentacion_briquetas.id,
                    almacen_id=lote.almacen_id,
                    cantidad=0
                )
                db.session.add(inventario)
            
            inventario.cantidad += data["cantidad_kg"]  # Añadir merma como briquetas
        
        db.session.commit()
        return merma_schema.dump(nueva_merma), 201

    @jwt_required()
    @handle_db_errors
    def put(self, merma_id):
        merma = Merma.query.get_or_404(merma_id)
        data = merma_schema.load(request.get_json(), partial=True)
        
        # Validar cambios críticos
        if "lote_id" in data and data["lote_id"] != merma.lote_id:
            return {"error": "No se puede modificar el lote asociado a una merma"}, 400
        
        # Actualizar campos permitidos
        for key, value in data.items():
            setattr(merma, key, value)
        
        db.session.commit()
        return merma_schema.dump(merma), 200

    @jwt_required()
    @handle_db_errors
    def delete(self, merma_id):
        merma = Merma.query.get_or_404(merma_id)
        
        # Revertir inventario si se había convertido a briquetas
        if merma.convertido_a_briquetas:
            presentacion_briquetas = PresentacionProducto.query.filter_by(
                tipo="briqueta"
            ).first()
            
            if presentacion_briquetas:
                inventario = Inventario.query.filter_by(
                    presentacion_id=presentacion_briquetas.id,
                    almacen_id=merma.lote.almacen_id
                ).first()
                
                if inventario:
                    inventario.cantidad -= merma.cantidad_kg
        
        db.session.delete(merma)
        db.session.commit()
        return "", 204