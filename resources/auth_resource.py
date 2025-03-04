from flask_restful import Resource, reqparse
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash
from models import Users, Almacen
from extensions import db
from flask import request, jsonify, abort
import datetime

class AuthResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True, help='El nombre de usuario es requerido')
        parser.add_argument('password', type=str, required=True, help='La contraseña es requerida')
        
        data = parser.parse_args()
        
        # Find user by username
        usuario = Users.query.filter_by(username=data['username']).first()
        
        # Check if user exists and password is correct
        if usuario and check_password_hash(usuario.password, data['password']):
            # Create JWT token with additional claims
            access_token = create_access_token(
                identity=str(usuario.id),
                additional_claims={
                    'username': usuario.username,
                    'rol': usuario.rol,
                    'almacen_id': usuario.almacen_id
                }
            )
            
            # Obtener nombre del almacén si existe
            nombre_almacen = None
            if usuario.almacen_id:
                almacen = Almacen.query.get(usuario.almacen_id)
                if almacen:
                    nombre_almacen = almacen.nombre
            
            return {
                'access_token': access_token,
                'token_type': 'Bearer',
                'user': {
                    'id': usuario.id,
                    'username': usuario.username,
                    'rol': usuario.rol,
                    'almacen_id': usuario.almacen_id,
                    'almacen_nombre': nombre_almacen
                }
            }, 200
        
        return {'message': 'Credenciales inválidas'}, 401


class RegisterResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True, help='El nombre de usuario es requerido')
        parser.add_argument('password', type=str, required=True, help='La contraseña es requerida')
        parser.add_argument('rol', type=str, required=False, default='usuario', help='El rol del usuario')
        parser.add_argument('almacen_id', type=int, required=False, help='ID del almacén asignado')
        
        data = parser.parse_args()
        
        # Check if username is already taken
        if Users.query.filter_by(username=data['username']).first():
            return {'message': 'El nombre de usuario ya está en uso'}, 400
        
        # Validar el rol
        roles_validos = ['admin', 'gerente', 'usuario']
        if data['rol'] not in roles_validos:
            return {'message': f'Rol inválido. Debe ser uno de: {", ".join(roles_validos)}'}, 400
        
        # Validar el almacén si se proporciona
        if data['almacen_id']:
            almacen = Almacen.query.get(data['almacen_id'])
            if not almacen:
                return {'message': 'El almacén especificado no existe'}, 400
        
        # Create new user
        nuevo_usuario = Users(
            username=data['username'],
            password=generate_password_hash(data['password']),
            rol=data['rol'],
            almacen_id=data['almacen_id']
        )
        
        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            return {'message': 'Usuario registrado exitosamente', 'id': nuevo_usuario.id}, 201
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error al registrar el usuario', 'error': str(e)}, 500