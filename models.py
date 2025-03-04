from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint
from datetime import datetime
from extensions import db 

# Tabla de Usuarios (para autenticación JWT)
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

    rol = db.Column(db.String(20), nullable=False, default='usuario')  # Valores: 'admin', 'gerente', 'usuario'
    almacen_id = db.Column(db.Integer, db.ForeignKey('almacenes.id', ondelete='SET NULL'), nullable=True)
    # Relación con almacén
    almacen = db.relationship('Almacen', backref=db.backref('usuarios', lazy=True))

    def __repr__(self):
        return f'<User {self.username}>'

# Modelo para la tabla productos
class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    precio_compra = db.Column(db.Numeric(12, 2), nullable=False)
    activo = db.Column(db.Boolean, default=True)  # Indica si el producto está disponible
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return f'<Producto {self.nombre}>'

# Modelo para la tabla almacenes
class Almacen(db.Model):
    __tablename__ = 'almacenes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    direccion = db.Column(db.Text)
    ciudad = db.Column(db.String(100))

    # Relación con iunventario
    inventario = db.relationship('Inventario', backref='almacen', lazy=True)

    def __repr__(self):
        return f'<Almacen {self.nombre}>'

# Tabla de inventario (stock por almacén)
class Inventario(db.Model):
    __tablename__ = 'inventario'
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id', ondelete='CASCADE'), primary_key=True)
    almacen_id = db.Column(db.Integer, db.ForeignKey('almacenes.id', ondelete='CASCADE'), primary_key=True)
    cantidad = db.Column(db.Integer, nullable=False, default=0)
    stock_minimo = db.Column(db.Integer, nullable=False, default=5)
    ultima_actualizacion = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('producto_id', 'almacen_id', name='uq_producto_almacen'),
    )

# Modelo para la tabla clientes
class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    ventas = db.relationship('Venta', backref='cliente', lazy=True)

    @property
    def saldo_pendiente(self):
        return sum(v.total for v in self.ventas if v.estado_pago != 'pagado')

    def __repr__(self):
        return f'<Cliente {self.nombre}>'

# Modelo para la tabla ventas
class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id', ondelete='CASCADE'), nullable=False)
    almacen_id = db.Column(db.Integer, db.ForeignKey('almacenes.id', ondelete='CASCADE'), nullable=False)
    fecha = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    total = db.Column(db.Numeric(12, 2), nullable=False)
    tipo_pago = db.Column(db.String(10), nullable=False)
    estado_pago = db.Column(db.String(15), default='pendiente')

    detalles = db.relationship('VentaDetalle', backref='venta', lazy=True)
    pagos = db.relationship("Pago", backref="venta", lazy=True, cascade="all, delete-orphan")

    # Restricciones
    __table_args__ = (
        CheckConstraint("tipo_pago IN ('contado', 'credito')"),
        CheckConstraint("estado_pago IN ('pendiente', 'parcial', 'pagado')")
    )

    # Campos calculados (no se almacenan en la DB)
    @property
    def monto_pagado(self):
        return sum(pago.monto for pago in self.pagos)  # Suma de todos los pagos

    @property
    def saldo_pendiente(self):
        return self.total - self.monto_pagado

    def actualizar_estado(self):
        if self.saldo_pendiente <= 0:
            self.estado_pago = "pagado"
        elif self.monto_pagado > 0:
            self.estado_pago = "parcial"
        else:
            self.estado_pago = "pendiente"

    def __repr__(self):
        return f'<Venta {self.id}>'
    
class Pago(db.Model):
    __tablename__ = "pagos"
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False) 
    fecha = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    metodo_pago = db.Column(db.String(20))  # "efectivo", "transferencia", "tarjeta"
    referencia = db.Column(db.String(50))  # Número de transacción o comprobante

# Detalle de ventas (productos vendidos)
class VentaDetalle(db.Model):
    __tablename__ = 'venta_detalles'
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id', ondelete='CASCADE'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id', ondelete='CASCADE'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    fecha_reabastecimiento = db.Column(db.Date)  # Fecha estimada para nuevo pedido

    producto = db.relationship('Producto')

# Modelo para la tabla movimientos
class Movimiento(db.Model):
    __tablename__ = 'movimientos'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id', ondelete='CASCADE'), nullable=False)
    almacen_id = db.Column(db.Integer, db.ForeignKey('almacenes.id', ondelete='CASCADE'), nullable=False)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id', ondelete='SET NULL'))
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id', ondelete='SET NULL'))
    cantidad = db.Column(db.Numeric(12, 2), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)
    fecha = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("cantidad > 0"),
        CheckConstraint("tipo IN ('entrada', 'salida')")
    )

    producto = db.relationship('Producto')
    almacen = db.relationship('Almacen')
    venta = db.relationship('Venta')
    proveedor = db.relationship('Proveedor')

class Proveedor(db.Model):
    __tablename__ = 'proveedores'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return f'<Proveedor {self.nombre}>'

# Modelo para la tabla gastos
class Gasto(db.Model):
    __tablename__ = 'gastos'
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text, nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    fecha = db.Column(db.Date, default=datetime.utcnow().date())
    categoria = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<Gasto {self.id}>'
    


