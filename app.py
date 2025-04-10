from flask import Flask, jsonify, send_from_directory
from flask_restful import Api
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from resources.auth_resource import AuthResource, RegisterResource
from resources.producto_resource import ProductoResource
from resources.proveedor_resource import ProveedorResource
from resources.almacen_resource import AlmacenResource
from resources.cliente_resource import ClienteResource
from resources.pago_resource import PagoResource
from resources.gasto_resource import GastoResource
from resources.movimiento_resource import MovimientoResource
from resources.venta_resource import VentaResource
from resources.user_resource import UserResource
from resources.inventario_resource import InventarioResource
from resources.lote_resource import LoteResource
from resources.merma_resource import MermaResource
from resources.presentacion_resource import PresentacionResource
from resources.pedido_resource import PedidoResource, PedidoConversionResource

from extensions import db, jwt
import os
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO if os.environ.get('FLASK_ENV') == 'production' else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuración de CORS - en producción limitar orígenes
allowed_origins = os.environ.get('ALLOWED_ORIGINS', '*')
CORS(app, resources={r"/*": {"origins": allowed_origins.split(',') if ',' in allowed_origins else allowed_origins}})

# Configuración de la base de datos desde variables de entorno
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:123456@localhost/manngo_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración para el manejo de archivos
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # Default 16MB max
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'pdf'}

# Crear directorio de uploads si no existe y estamos en modo local
if os.environ.get('STORAGE_MODE', 'local') == 'local':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'presentaciones'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'comprobantes'), exist_ok=True)

# JWT config con valores seguros
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.environ.get('JWT_EXPIRES_SECONDS', 43200))  # Default 12 horas
app.config['JWT_ALGORITHM'] = 'HS256'
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')  # SIEMPRE usar variable de entorno
app.config['JWT_BLACKLIST_ENABLED'] = True

if app.config['JWT_SECRET_KEY'] is None or app.config['JWT_SECRET_KEY'] == 'insecure-key':
    if os.environ.get('FLASK_ENV') == 'production':
        raise ValueError("JWT_SECRET_KEY no configurada en producción - ¡Configure una clave segura!")
    else:
        logger.warning("⚠️ Usando clave JWT insegura para desarrollo, no usar en producción")
        app.config['JWT_SECRET_KEY'] = 'insecure-dev-key'

# Inicializar extensiones
db.init_app(app)
jwt.init_app(app)
api = Api(app)

# JWT Error handling
@jwt.unauthorized_loader
def unauthorized_callback(callback):
    logger.warning(f"Unauthorized request: {callback}")
    return jsonify({
        'message': 'Se requiere autenticación',
        'error': 'authorization_required'
    }), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    logger.warning(f"Expired token: {jwt_payload}")
    return jsonify({
        'message': 'El token ha expirado',
        'error': 'token_expired'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    logger.error(f"Invalid token: {error}")
    return jsonify({
        'message': 'Verificación de firma fallida',
        'error': 'invalid_token'
    }), 401

@app.errorhandler(500)
def handle_internal_server_error(e):
    logger.exception(f"Internal server error: {e}")
    return jsonify({
        "error": "Ocurrió un error interno del servidor",
        "details": str(e) if os.environ.get('FLASK_ENV') != 'production' else "Contacte al administrador"
    }), 500

@app.errorhandler(404)
def handle_not_found_error(e):
    return jsonify({"error": "Recurso no encontrado"}), 404

@app.errorhandler(405)
def handle_method_not_allowed(e):
    return jsonify({"error": "Método no permitido"}), 405

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Sirve archivos subidos"""
    if '../' in filename or filename.startswith('/'):
        return jsonify({"error": "Acceso denegado"}), 403
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({"status": "ok"}), 200

# Registrar recursos
api.add_resource(AuthResource, '/auth')
api.add_resource(RegisterResource, '/registrar')
api.add_resource(UserResource, '/usuarios', '/usuarios/<int:user_id>')
api.add_resource(ProductoResource, '/productos', '/productos/<int:producto_id>')
api.add_resource(PagoResource, '/pagos', '/pagos/<int:pago_id>')
api.add_resource(ProveedorResource, '/proveedores', '/proveedores/<int:proveedor_id>')
api.add_resource(AlmacenResource, '/almacenes', '/almacenes/<int:almacen_id>')
api.add_resource(ClienteResource, '/clientes', '/clientes/<int:cliente_id>')
api.add_resource(GastoResource, '/gastos', '/gastos/<int:gasto_id>')
api.add_resource(MovimientoResource, '/movimientos', '/movimientos/<int:movimiento_id>')
api.add_resource(VentaResource, '/ventas', '/ventas/<int:venta_id>')
api.add_resource(InventarioResource, '/inventarios', '/inventarios/<int:inventario_id>')
api.add_resource(PresentacionResource, '/presentaciones', '/presentaciones/<int:presentacion_id>')
api.add_resource(MermaResource, '/mermas', '/mermas/<int:merma_id>')
api.add_resource(LoteResource, '/lotes', '/lotes/<int:lote_id>')
api.add_resource(PedidoResource, '/pedidos', '/pedidos/<int:pedido_id>')
api.add_resource(PedidoConversionResource, '/pedidos/<int:pedido_id>/convertir')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV', 'development') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)