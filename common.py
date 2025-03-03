# common.py
from flask import jsonify
from marshmallow import ValidationError
from extensions import db

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