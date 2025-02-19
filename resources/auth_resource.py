
from extensions import db 
from models import User
from flask_jwt_extended import create_access_token
from flask_restful import Resource, reqparse
from werkzeug.security import generate_password_hash, check_password_hash

class AuthResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        args = parser.parse_args()
        user = User.query.filter_by(username=args['username']).first()
        
        if user and check_password_hash(user.password, args['password']):
            access_token = create_access_token(identity=user.id)
            return {'access_token': access_token}, 200
        
        return {'message': 'Credenciales inválidas'}, 401
    
class RegisterResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        args = parser.parse_args()

        # Verifica si el usuario ya existe
        if User.query.filter_by(username=args['username']).first():
            return {'message': 'El nombre de usuario ya está en uso'}, 400

        # Crea un nuevo usuario
        hashed_password = generate_password_hash(args['password'])
        nuevo_usuario = User(username=args['username'], password=hashed_password)
        db.session.add(nuevo_usuario)
        db.session.commit()

        return {'message': 'Usuario registrado exitosamente'}, 201