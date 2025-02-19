from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from flask import jsonify
from flask_jwt_extended import JWTManager
from resources.auth_resource import AuthResource, RegisterResource
from resources.producto_resource import ProductoResource
from resources.almacen_resource import AlmacenResource
from resources.cliente_resource import ClienteResource
from resources.gasto_resource import GastoResource
from resources.movimiento_resource import MovimientoResource
from resources.venta_resource import VentaResource
from extensions import db  # Importa la instancia de SQLAlchemy

app = Flask(__name__)

# Configuración de CORS
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@localhost/invManngo'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False




# Configuración de JWT
app.config['JWT_SECRET_KEY'] = 'mamahuevo' 

db.init_app(app)
jwt = JWTManager(app)  # Inicializa JWTManager
api = Api(app)

@app.errorhandler(500)
def handle_internal_server_error(e):
    return jsonify({"error": "Ocurrió un error interno del servidor", "details": str(e)}), 500
# Registrar recursos
api.add_resource(AuthResource, '/auth')
api.add_resource(RegisterResource, '/registrar')
api.add_resource(ProductoResource, '/productos', '/productos/<int:producto_id>')
api.add_resource(AlmacenResource, '/almacenes', '/almacenes/<int:almacen_id>')
api.add_resource(ClienteResource, '/clientes', '/clientes/<int:cliente_id>')
api.add_resource(GastoResource, '/gastos', '/gastos/<int:gasto_id>')
api.add_resource(MovimientoResource, '/movimientos', '/movimientos/<int:movimiento_id>')
api.add_resource(VentaResource, '/ventas', '/ventas/<int:venta_id>')

if __name__ == '__main__':
    app.run(debug=True)