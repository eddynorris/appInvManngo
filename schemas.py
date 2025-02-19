from marshmallow import Schema, fields, EXCLUDE
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from decimal import Decimal
from models import User, Producto, Almacen, Cliente, Gasto, Movimiento, Venta  # Importa tus modelos
from extensions import db

class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True  # Permite cargar instancias del modelo
        include_fk = True  # Incluye claves foráneas
        unknown = EXCLUDE  # Ignora campos desconocidos

class ProductoSchema(SQLAlchemyAutoSchema):
    precio_compra = fields.Decimal(as_string=True)  # Convierte Decimal a cadena
    precio_venta = fields.Decimal(as_string=True)   # Convierte Decimal a cadena

    class Meta:
        model = Producto
        load_instance = True
        include_fk = True
        unknown = EXCLUDE
        sqla_session = db.session 

class AlmacenSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Almacen
        load_instance = True
        include_fk = True
        unknown = EXCLUDE

class ClienteSchema(SQLAlchemyAutoSchema):
    saldo_pendiente = fields.Decimal(as_string=True) 

    class Meta:
        model = Cliente
        load_instance = True
        include_fk = True
        unknown = EXCLUDE

class GastoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Gasto
        load_instance = True
        include_fk = True
        unknown = EXCLUDE

class MovimientoSchema(SQLAlchemyAutoSchema):
    producto = fields.Nested(ProductoSchema, only=("id", "nombre"))  # Solo incluye ID y nombre del producto
    almacen = fields.Nested(AlmacenSchema, only=("id", "nombre"))  # Solo incluye ID y nombre del almacén
    venta = fields.Nested("VentaSchema", only=("id", "total"), allow_none=True)  # Relación opcional con ventas

    class Meta:
        model = Movimiento
        load_instance = True
        include_fk = True
        unknown = EXCLUDE

class VentaSchema(SQLAlchemyAutoSchema):
    cliente = fields.Nested(ClienteSchema, only=("id", "nombre"))  # Solo incluye ID y nombre del cliente
    productos = fields.List(fields.Nested({
        "producto_id": fields.Int(required=True),
        "cantidad": fields.Decimal(required=True, places=2)
    }), required=True)  # Lista de productos vendidos

    class Meta:
        model = Venta
        load_instance = True
        include_fk = True
        unknown = EXCLUDE

# Inicializar esquemas
user_schema = UserSchema()
users_schema = UserSchema(many=True)

producto_schema = ProductoSchema()
productos_schema = ProductoSchema(many=True)

almacen_schema = AlmacenSchema()
almacenes_schema = AlmacenSchema(many=True)

cliente_schema = ClienteSchema()
clientes_schema = ClienteSchema(many=True)

gasto_schema = GastoSchema()
gastos_schema = GastoSchema(many=True)

movimiento_schema = MovimientoSchema()
movimientos_schema = MovimientoSchema(many=True)

venta_schema = VentaSchema()
ventas_schema = VentaSchema(many=True)