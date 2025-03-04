from marshmallow import Schema, fields, EXCLUDE
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from decimal import Decimal
from models import Users, Producto, Almacen, Cliente, Gasto, Movimiento, Venta, VentaDetalle, Proveedor, Pago, Inventario
from extensions import db

# Esquema para el modelo Almacen
class AlmacenSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Almacen
        load_instance = True
        include_fk = True
        unknown = EXCLUDE
        sqla_session = db.session

# Esquema para el modelo User
class UserSchema(SQLAlchemyAutoSchema):
    almacen = fields.Nested(AlmacenSchema, only=("id", "nombre"), dump_only=True)

    class Meta:
        model = Users
        load_instance = True  # Permite cargar instancias del modelo
        include_fk = True  # Incluye claves foráneas
        unknown = EXCLUDE  # Ignora campos desconocidos

    
# Esquema para el modelo Proveedor
class ProveedorSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Proveedor
        load_instance = True
        include_fk = True
        unknown = EXCLUDE
        sqla_session = db.session

# Esquema para el modelo Producto
class ProductoSchema(SQLAlchemyAutoSchema):
    precio_compra = fields.Decimal(as_string=True)  # Convierte Decimal a cadena

    class Meta:
        model = Producto
        load_instance = True
        include_fk = True
        unknown = EXCLUDE
        sqla_session = db.session

# Esquema para el modelo Cliente
class ClienteSchema(SQLAlchemyAutoSchema):
    saldo_pendiente = fields.Decimal(as_string=True, dump_only=True)  # Calculado dinámicamente

    class Meta:
        model = Cliente
        load_instance = True
        include_fk = True
        unknown = EXCLUDE
        sqla_session = db.session

# Esquema para el modelo Gasto
class GastoSchema(SQLAlchemyAutoSchema):
    monto = fields.Decimal(as_string=True)  # Calculado dinámicamente

    class Meta:
        model = Gasto
        load_instance = True
        include_fk = True
        unknown = EXCLUDE
        sqla_session = db.session

# Esquema para el modelo Movimiento
class MovimientoSchema(SQLAlchemyAutoSchema):
    producto = fields.Nested(ProductoSchema, only=("id", "nombre"))  # Solo incluye ID y nombre del producto
    almacen = fields.Nested(AlmacenSchema, only=("id", "nombre"))  # Solo incluye ID y nombre del almacén
    venta = fields.Nested("VentaSchema", only=("id", "total"), allow_none=True)  # Relación opcional con ventas
    proveedor = fields.Nested("ProveedorSchema", only=("id", "nombre"), allow_none=True)  # Relación opcional con proveedores

    class Meta:
        model = Movimiento
        load_instance = True
        include_fk = True
        unknown = EXCLUDE
        sqla_session = db.session

# Esquema para el modelo PagoSchema
class PagoSchema(SQLAlchemyAutoSchema):
    monto = fields.Decimal(as_string=True, dump_only=True)  # Calculado dinámicamente
    class Meta:
        model = Pago
        load_instance = True
        include_fk = True
        unknown = EXCLUDE
        sqla_session = db.session

# Esquema para el modelo Venta
class VentaSchema(SQLAlchemyAutoSchema):
    cliente = fields.Nested(ClienteSchema, only=("id", "nombre"))  # Solo incluye ID y nombre del cliente
    almacen = fields.Nested(AlmacenSchema, only=("id", "nombre"))  # Solo incluye ID y nombre del almacén
    pagos = fields.List(fields.Nested(PagoSchema()), dump_only=True)  # Lista de pagos
    
    detalles = fields.List(fields.Nested("VentaDetalleSchema"))  # Lista de detalles de venta
    monto_pagado = fields.Decimal(as_string=True, dump_only=True)  # Campo calculado
    saldo_pendiente = fields.Decimal(as_string=True, dump_only=True)  # Campo calculado
    
    total = fields.Decimal(as_string=True)

    class Meta:
        model = Venta
        load_instance = True
        include_fk = True
        unknown = EXCLUDE
        sqla_session = db.session

# Esquema para el modelo VentaDetalle
class VentaDetalleSchema(SQLAlchemyAutoSchema):
    producto = fields.Nested(ProductoSchema, only=("id", "nombre"))  # Solo incluye ID y nombre del producto

    class Meta:
        model = VentaDetalle
        load_instance = True
        include_fk = True
        unknown = EXCLUDE
        sqla_session = db.session
        exclude = ("venta",)

# Inicializar esquemas
user_schema = UserSchema()
users_schema = UserSchema(many=True)

proveedor_schema = ProveedorSchema()
proveedores_schema = ProveedorSchema(many=True)

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

pago_schema = PagoSchema()
pagos_schema = PagoSchema(many=True)

venta_detalle_schema = VentaDetalleSchema()
ventas_detalle_schema = VentaDetalleSchema(many=True)