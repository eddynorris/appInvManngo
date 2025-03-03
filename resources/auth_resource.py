from flask_restful import Resource, reqparse
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash
from models import Users
from extensions import db
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
            # Create JWT token - IMPORTANT: Convert user ID to string
            access_token = create_access_token(
                identity=str(usuario.id),  # Convert to string!
                additional_claims={
                    'username': usuario.username,
                    # Add any other claims you need
                }
            )
            
            return {
                'access_token': access_token,
                'token_type': 'Bearer'
            }, 200
        
        return {'message': 'Credenciales inválidas'}, 401


class RegisterResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True, help='El nombre de usuario es requerido')
        parser.add_argument('password', type=str, required=True, help='La contraseña es requerida')
        
        data = parser.parse_args()
        
        # Check if username is already taken
        if Users.query.filter_by(username=data['username']).first():
            return {'message': 'El nombre de usuario ya está en uso'}, 400
        
        # Create new user
        nuevo_usuario = Users(
            username=data['username'],
            password=generate_password_hash(data['password'])
        )
        
        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            return {'message': 'Users registrado exitosamente'}, 201
        except Exception as e:
            db.session.rollback()
            return {'message': 'Error al registrar el usuario', 'error': str(e)}, 500