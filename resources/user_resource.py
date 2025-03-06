# Archivo: resources/user_resource.py
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt
from flask import request
from models import Users
from schemas import user_schema, users_schema
from extensions import db
from common import handle_db_errors, MAX_ITEMS_PER_PAGE, rol_requerido
from werkzeug.security import generate_password_hash

class UserResource(Resource):
    @jwt_required()
    @rol_requerido('admin')
    @handle_db_errors
    def get(self, user_id=None):      
        # Si se solicita un usuario específico
        if user_id:
            usuario = Users.query.get_or_404(user_id)
            return user_schema.dump(usuario), 200
        
        # Permitir filtrar por rol o almacén
        query = Users.query
        
        # Filtrar por rol si se especifica
        rol = request.args.get('rol')
        if rol:
            query = query.filter(Users.rol == rol)
        
        # Filtrar por almacén si se especifica
        almacen_id = request.args.get('almacen_id')
        if almacen_id:
            query = query.filter(Users.almacen_id == almacen_id)
        
        # Paginación
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), MAX_ITEMS_PER_PAGE)
        usuarios = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            "data": users_schema.dump(usuarios.items),
            "pagination": {  # Estructura corregida
                "total": usuarios.total,
                "page": usuarios.page,
                "per_page": usuarios.per_page,
                "pages": usuarios.pages
            }
        }, 200

    @jwt_required()
    @rol_requerido('admin')
    @handle_db_errors
    def post(self):
        data = request.get_json()
        
        # Verificar que el username no exista
        if Users.query.filter_by(username=data.get('username')).first():
            return {"message": "El nombre de usuario ya existe"}, 400
        
        # Hashear la contraseña
        if 'password' in data:
            data['password'] = generate_password_hash(data['password'])
        
        # Validar rol
        if data.get('rol') not in ['admin', 'gerente', 'usuario']:
            return {"message": "Rol inválido. Debe ser admin, gerente o usuario"}, 400
        
        # Crear usuario
        nuevo_usuario = user_schema.load(data)
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        return user_schema.dump(nuevo_usuario), 201

    @jwt_required()
    @rol_requerido('admin')
    @handle_db_errors
    def put(self, user_id):
        usuario = Users.query.get_or_404(user_id)
        data = request.get_json()
        
        # Si se cambia el username, verificar que no exista
        if 'username' in data and data['username'] != usuario.username:
            if Users.query.filter_by(username=data['username']).first():
                return {"message": "El nombre de usuario ya existe"}, 400
        
        # Hashear la contraseña si se proporciona
        if 'password' in data:
            data['password'] = generate_password_hash(data['password'])
        
        # Validar rol si se proporciona
        if 'rol' in data and data['rol'] not in ['admin', 'gerente', 'usuario']:
            return {"message": "Rol inválido. Debe ser admin, gerente o usuario"}, 400
        
        # Actualizar usuario
        updated_usuario = user_schema.load(data, instance=usuario, partial=True)
        db.session.commit()
        
        return user_schema.dump(updated_usuario), 200

    @jwt_required()
    @rol_requerido('admin')
    @handle_db_errors
    def delete(self, user_id):
        usuario = Users.query.get_or_404(user_id)
        
        # No permitir eliminar al usuario que hace la petición
        claims = get_jwt()
        if str(usuario.id) == claims.get('sub'):
            return {"message": "No puedes eliminar tu propio usuario"}, 400
        
        db.session.delete(usuario)
        db.session.commit()
        
        return {"message": "Usuario eliminado correctamente"}, 200