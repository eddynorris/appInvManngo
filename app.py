from flask import Flask, jsonify
from flask_restful import Api
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from resources.auth_resource import AuthResource, RegisterResource
from resources.producto_resource import ProductoResource
from resources.proveedor_resource import ProveedorResource
from resources.almacen_resource import AlmacenResource
from resources.cliente_resource import ClienteResource
from resources.gasto_resource import GastoResource
from resources.movimiento_resource import MovimientoResource
from resources.venta_resource import VentaResource
from extensions import db, jwt  # Importa la instancia de SQLAlchemy
import os
import logging
import secrets

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuración de CORS
CORS(app, resources={r"/*": {"origins": "*"}})

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@localhost/db_manngo'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Generate a secure secret key (do this only once and then store it)
# For production, store this in an environment variable instead
# generated_secret_key = secrets.token_hex(32)
# print(f"Generated secret key: {generated_secret_key}")

# Use environment variable or fallback to a hardcoded key (for development only)


# Additional JWT configuration for better security
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 6000  # Token expires in 1 hour
app.config['JWT_ALGORITHM'] = 'HS256'  # Specify the algorithm
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'mamahuevo')


db.init_app(app)
jwt.init_app(app)  # Inicializa JWTManager
api = Api(app)

# JWT Error handling
@jwt.unauthorized_loader
def unauthorized_callback(callback):
    logger.warning(f"Unauthorized request: {callback}")
    return jsonify({
        'message': 'Missing or invalid Authorization header',
        'error': 'authorization_required'
    }), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    logger.warning(f"Expired token: {jwt_payload}")
    return jsonify({
        'message': 'The token has expired',
        'error': 'token_expired'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    logger.error(f"Invalid token: {error}")
    return jsonify({
        'message': 'Signature verification failed',
        'error': 'invalid_token'
    }), 401

@app.errorhandler(500)
def handle_internal_server_error(e):
    logger.exception(f"Internal server error: {e}")
    return jsonify({
        "error": "Ocurrió un error interno del servidor", 
        "details": str(e)
    }), 500

# Registrar recursos
api.add_resource(AuthResource, '/auth')
api.add_resource(RegisterResource, '/registrar')
api.add_resource(ProductoResource, '/productos', '/productos/<int:producto_id>')
api.add_resource(ProveedorResource, '/proveedores', '/proveedores/<int:proveedor_id>')
api.add_resource(AlmacenResource, '/almacenes', '/almacenes/<int:almacen_id>')
api.add_resource(ClienteResource, '/clientes', '/clientes/<int:cliente_id>')
api.add_resource(GastoResource, '/gastos', '/gastos/<int:gasto_id>')
api.add_resource(MovimientoResource, '/movimientos', '/movimientos/<int:movimiento_id>')
api.add_resource(VentaResource, '/ventas', '/ventas/<int:venta_id>')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)