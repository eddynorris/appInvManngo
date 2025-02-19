from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint
from datetime import datetime
from extensions import db 

# Tabla de Usuarios (para autenticación JWT)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

# Modelo para la tabla productos
class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    precio_compra = db.Column(db.Numeric(12, 2), nullable=False)
    precio_venta = db.Column(db.Numeric(12, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    stock_minimo = db.Column(db.Integer, nullable=False, default=5)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    
    # Relación con movimientos
    movimientos = db.relationship('Movimiento', backref='producto', lazy=True)

    def __repr__(self):
        return f'<Producto {self.nombre}>'

# Modelo para la tabla almacenes
class Almacen(db.Model):
    __tablename__ = 'almacenes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    direccion = db.Column(db.Text)
    ciudad = db.Column(db.String(100))

    # Relación con movimientos
    movimientos = db.relationship('Movimiento', backref='almacen', lazy=True)

    def __repr__(self):
        return f'<Almacen {self.nombre}>'

# Modelo para la tabla clientes
class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.Text)
    saldo_pendiente = db.Column(db.Numeric(12, 2), default=0)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    # Relación con ventas
    ventas = db.relationship('Venta', backref='cliente', lazy=True)

    def __repr__(self):
        return f'<Cliente {self.nombre}>'

# Modelo para la tabla ventas
class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id', ondelete='CASCADE'), nullable=False)
    fecha = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    total = db.Column(db.Numeric(12, 2), nullable=False)
    tipo_pago = db.Column(db.String(10), nullable=False)
    fecha_vencimiento = db.Column(db.Date)
    estado_pago = db.Column(db.String(15), default='pendiente')

    # Restricciones
    __table_args__ = (
        CheckConstraint("tipo_pago IN ('contado', 'credito')"),
        CheckConstraint("estado_pago IN ('pendiente', 'parcial', 'pagado')")
    )

    # Relación con movimientos
    movimientos = db.relationship('Movimiento', backref='venta', lazy=True)

    def __repr__(self):
        return f'<Venta {self.id}>'

# Modelo para la tabla movimientos
class Movimiento(db.Model):
    __tablename__ = 'movimientos'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id', ondelete='CASCADE'), nullable=False)
    almacen_id = db.Column(db.Integer, db.ForeignKey('almacenes.id', ondelete='CASCADE'), nullable=False)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id', ondelete='CASCADE'))
    cantidad = db.Column(db.Numeric(12, 2), nullable=False)
    precio_venta = db.Column(db.Numeric(12, 2), nullable=False)  # Precio histórico
    tipo = db.Column(db.String(10), nullable=False)
    fecha = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    # Restricciones
    __table_args__ = (
        CheckConstraint("cantidad > 0"),
        CheckConstraint("tipo IN ('entrada', 'salida')")
    )

    def __repr__(self):
        return f'<Movimiento {self.id}>'

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