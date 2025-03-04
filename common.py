# common.py
from flask import jsonify
from marshmallow import ValidationError
from extensions import db
from functools import wraps
from flask_jwt_extended import get_jwt
from flask import jsonify

MAX_ITEMS_PER_PAGE = 100

def handle_db_errors(func):
    """Decorator para manejo centralizado de errores"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            return {"message": "Datos inválidos", "errors": e.messages}, 400
        except Exception as e:
            db.session.rollback()
            print(f"Error en {func.__name__}: {str(e)}")
            return {"message": "Error interno del servidor"}, 500
    return wrapper

def rol_requerido(roles_permitidos):
    """
    Decorador para verificar si el usuario tiene un rol permitido
    Ejemplo de uso: @rol_requerido(['admin', 'gerente'])
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Obtener los claims del token JWT
            claims = get_jwt()
            
            # Verificar si el rol está en la lista de roles permitidos
            if claims.get('rol') not in roles_permitidos:
                return jsonify({
                    'message': 'No tiene permiso para acceder a este recurso',
                    'error': 'acceso_denegado'
                }), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def mismo_almacen_o_admin(fn):
    """
    Decorador para verificar si el usuario tiene acceso al almacén solicitado
    - Si es admin, tiene acceso a todos los almacenes
    - Si no es admin, solo tiene acceso a su propio almacén
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Obtener los claims del token JWT
        claims = get_jwt()
        
        # Si es admin, permitir acceso
        if claims.get('rol') == 'admin':
            return fn(*args, **kwargs)
        
        # Verificar si está intentando acceder a datos de otro almacén
        almacen_id_request = kwargs.get('almacen_id')
        if almacen_id_request and int(almacen_id_request) != claims.get('almacen_id'):
            return jsonify({
                'message': 'No tiene permiso para acceder a este almacén',
                'error': 'acceso_denegado'
            }), 403
        
        return fn(*args, **kwargs)
    return wrapper