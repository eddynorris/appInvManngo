from marshmallow import Schema, fields, EXCLUDE
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models import (
    Users, Producto, Almacen, Cliente, Gasto, Movimiento, 
    Venta, VentaDetalle, Proveedor, Pago, Inventario,
    PresentacionProducto, Lote, Merma  # Nuevos modelos
)
from extensions import db

# ------------------------- ESQUEMAS BASE -------------------------
class AlmacenSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Almacen
        load_instance = True
        unknown = EXCLUDE
        exclude = ("inventario", "ventas")  # Excluir relaciones recursivas

class ProveedorSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Proveedor
        load_instance = True
        unknown = EXCLUDE

# ------------------------- ESQUEMAS PARA NUEVOS MODELOS -------------------------
class PresentacionProductoSchema(SQLAlchemyAutoSchema):
    producto = fields.Nested("ProductoSchema", only=("id", "nombre"), dump_only=True)
    
    class Meta:
        model = PresentacionProducto
        load_instance = True
        unknown = EXCLUDE
        include_fk = True  # Incluir producto_id

class LoteSchema(SQLAlchemyAutoSchema):
    proveedor = fields.Nested(ProveedorSchema, only=("id", "nombre"), dump_only=True)
    producto = fields.Nested("ProductoSchema", only=("id", "nombre"), dump_only=True)

    class Meta:
        model = Lote
        load_instance = True
        unknown = EXCLUDE

class MermaSchema(SQLAlchemyAutoSchema):
    lote = fields.Nested(LoteSchema, only=("id", "peso_seco_kg"), dump_only=True)

    class Meta:
        model = Merma
        load_instance = True
        unknown = EXCLUDE

# ------------------------- ESQUEMAS ACTUALIZADOS -------------------------
class ProductoSchema(SQLAlchemyAutoSchema):
    presentaciones = fields.List(fields.Nested(PresentacionProductoSchema, exclude=("producto",)), dump_only=True)
    precio_compra = fields.Decimal(as_string=True)

    class Meta:
        model = Producto
        load_instance = True
        unknown = EXCLUDE

class InventarioSchema(SQLAlchemyAutoSchema):
    presentacion = fields.Nested(PresentacionProductoSchema, only=("id", "nombre", "capacidad_kg"))
    almacen = fields.Nested(AlmacenSchema, only=("id", "nombre"))
    lote = fields.Nested(LoteSchema, only=("id", "proveedor"))

    class Meta:
        model = Inventario
        load_instance = True
        unknown = EXCLUDE

class ClienteSchema(SQLAlchemyAutoSchema):
    saldo_pendiente = fields.Decimal(as_string=True, dump_only=True)
    ultima_fecha_compra = fields.DateTime(format="%Y-%m-%d")

    class Meta:
        model = Cliente
        load_instance = True
        unknown = EXCLUDE

class MovimientoSchema(SQLAlchemyAutoSchema):
    presentacion = fields.Nested(PresentacionProductoSchema, only=("id", "nombre"))
    lote = fields.Nested(LoteSchema, only=("id", "peso_seco_kg"))
    usuario = fields.Nested("UserSchema", only=("id", "username"))

    class Meta:
        model = Movimiento
        load_instance = True
        unknown = EXCLUDE

class VentaDetalleSchema(SQLAlchemyAutoSchema):
    presentacion = fields.Nested(PresentacionProductoSchema, only=("id", "nombre", "precio_venta"))
    precio_unitario = fields.Decimal(as_string=True)

    class Meta:
        model = VentaDetalle
        load_instance = True
        unknown = EXCLUDE
        exclude = ("venta_id",)

class VentaSchema(SQLAlchemyAutoSchema):
    cliente = fields.Nested(ClienteSchema, only=("id", "nombre"))
    almacen = fields.Nested(AlmacenSchema, only=("id", "nombre"))
    detalles = fields.List(fields.Nested(VentaDetalleSchema))
    consumo_diario_kg = fields.Decimal(as_string=True)
    saldo_pendiente = fields.Decimal(as_string=True, dump_only=True)

    class Meta:
        model = Venta
        load_instance = True
        unknown = EXCLUDE

class PagoSchema(SQLAlchemyAutoSchema):
    venta = fields.Nested(VentaSchema, only=("id", "total"))
    usuario = fields.Nested("UserSchema", only=("id", "username"))

    class Meta:
        model = Pago
        load_instance = True
        unknown = EXCLUDE

class UserSchema(SQLAlchemyAutoSchema):
    almacen = fields.Nested(AlmacenSchema, only=("id", "nombre"))

    class Meta:
        model = Users
        load_instance = True
        unknown = EXCLUDE

class GastoSchema(SQLAlchemyAutoSchema):
    almacen = fields.Nested(AlmacenSchema, only=("id", "nombre"))
    usuario = fields.Nested(UserSchema, only=("id", "username"))

    class Meta:
        model = Gasto
        load_instance = True
        unknown = EXCLUDE

# Inicializar esquemas
user_schema = UserSchema()
users_schema = UserSchema(many=True)

presentacion_schema = PresentacionProductoSchema()
presentaciones_schema = PresentacionProductoSchema(many=True)

lote_schema = LoteSchema()
lotes_schema = LoteSchema(many=True)

merma_schema = MermaSchema()
mermas_schema = MermaSchema(many=True)

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

inventario_schema = InventarioSchema()
inventarios_schema = InventarioSchema(many=True)