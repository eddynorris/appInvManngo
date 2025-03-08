from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint, Index
from datetime import datetime, timezone
from extensions import db
from decimal import Decimal

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='usuario')
    almacen_id = db.Column(db.Integer, db.ForeignKey('almacenes.id', ondelete='SET NULL'))
    
    movimientos = db.relationship('Movimiento', back_populates='usuario')

    def __repr__(self):
        return f'<User {self.username}>'

class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False, unique=True)  # Ej: "Carbón Vegetal Premium"
    descripcion = db.Column(db.Text)
    precio_compra = db.Column(db.Numeric(12, 2), nullable=False)  # Precio por tonelada al proveedor
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Producto {self.nombre}>'

class PresentacionProducto(db.Model):
    __tablename__ = 'presentaciones_producto'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id', ondelete='CASCADE'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)  # Ej: "Bolsa 5kg Supermercado"
    capacidad_kg = db.Column(db.Numeric(10, 2), nullable=False)  # Peso neto del producto
    tipo = db.Column(db.String(20), nullable=False)  # "bruto", "procesado", "merma", "briqueta", "detalle"
    precio_venta = db.Column(db.Numeric(12, 2), nullable=False)  # Precio al público
    activo = db.Column(db.Boolean, default=True)

    # Relaciones
    producto = db.relationship('Producto', backref=db.backref('presentaciones', lazy=True))

    __table_args__ = (
        CheckConstraint("tipo IN ('bruto', 'procesado', 'merma', 'briqueta', 'detalle')"),
        UniqueConstraint('producto_id', 'nombre', name='uq_producto_nombre_presentacion')
    )

class Lote(db.Model):
    __tablename__ = 'lotes'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id', ondelete='CASCADE'), nullable=False)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id', ondelete='SET NULL'), nullable=True)
    peso_humedo_kg = db.Column(db.Numeric(10, 2), nullable=False)  # Peso inicial (mojado)
    peso_seco_kg = db.Column(db.Numeric(10, 2))  # Peso real después de secado
    cantidad_disponible_kg = db.Column(db.Numeric(10, 2))
    fecha_ingreso = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relaciones
    producto = db.relationship('Producto', backref=db.backref('lotes', lazy=True))
    proveedor = db.relationship('Proveedor', backref=db.backref('lotes', lazy=True))

class Almacen(db.Model):
    __tablename__ = 'almacenes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    direccion = db.Column(db.Text)
    ciudad = db.Column(db.String(100))
    
    # Relaciones existentes (se mantienen)
    inventario = db.relationship('Inventario', backref='almacen', lazy=True)
    ventas = db.relationship('Venta', backref='almacen', lazy=True)

    def __repr__(self):
        return f'<Almacen {self.nombre}>'

class Inventario(db.Model):
    __tablename__ = 'inventario'
    id = db.Column(db.Integer, primary_key=True)  # PK autoincremental
    presentacion_id = db.Column(db.Integer, db.ForeignKey('presentaciones_producto.id', ondelete='CASCADE'), nullable=False)
    almacen_id = db.Column(db.Integer, db.ForeignKey('almacenes.id', ondelete='CASCADE'), nullable=False)
    lote_id = db.Column(db.Integer, db.ForeignKey('lotes.id', ondelete='SET NULL'))

    cantidad = db.Column(db.Integer, nullable=False, default=0)
    stock_minimo = db.Column(db.Integer, nullable=False, default=10)
    ultima_actualizacion = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relaciones
    presentacion = db.relationship('PresentacionProducto')
    lote = db.relationship('Lote')

    __table_args__ = (
        # Garantizar que no haya duplicados para la combinación de estos tres campos
        UniqueConstraint('presentacion_id', 'almacen_id', name='uq_inventario_compuesto'),
        
        # Índices para mejorar el rendimiento de consultas comunes
        Index('idx_inventario_almacen', 'almacen_id', 'presentacion_id'),
    )

class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id', ondelete='CASCADE'), nullable=False)
    almacen_id = db.Column(db.Integer, db.ForeignKey('almacenes.id', ondelete='CASCADE'), nullable=False)
    fecha = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    total = db.Column(db.Numeric(12, 2), nullable=False)
    tipo_pago = db.Column(db.String(10), nullable=False)
    estado_pago = db.Column(db.String(15), default='pendiente')
    consumo_diario_kg = db.Column(db.Numeric(10, 2))  # Estimación global para proyecciones

    # Relaciones
    detalles = db.relationship('VentaDetalle', backref='venta', lazy=True, cascade="all, delete-orphan")
    pagos = db.relationship("Pago", backref="venta", lazy=True, cascade="all, delete-orphan")

    @property
    def saldo_pendiente(self):
        total_pagado = sum(pago.monto for pago in self.pagos)
        return self.total - total_pagado

    def actualizar_estado(self):
        if self.saldo_pendiente <= 0:
            self.estado_pago = 'pagado'
        elif len(self.pagos) > 0:
            self.estado_pago = 'parcial'
        else:
            self.estado_pago = 'pendiente'

    __table_args__ = (
        CheckConstraint("tipo_pago IN ('contado', 'credito')"),
        CheckConstraint("estado_pago IN ('pendiente', 'parcial', 'pagado')")
    )

class VentaDetalle(db.Model):
    __tablename__ = 'venta_detalles'
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id', ondelete='CASCADE'), nullable=False)
    presentacion_id = db.Column(db.Integer, db.ForeignKey('presentaciones_producto.id', ondelete='CASCADE'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)  # Precio en el momento de la venta

    # Relación
    presentacion = db.relationship('PresentacionProducto')

    @property
    def total_linea(self):
        return self.cantidad * self.precio_unitario

class Merma(db.Model):
    __tablename__ = 'mermas'
    id = db.Column(db.Integer, primary_key=True)
    lote_id = db.Column(db.Integer, db.ForeignKey('lotes.id', ondelete='CASCADE'), nullable=False)
    cantidad_kg = db.Column(db.Numeric(10, 2), nullable=False)
    convertido_a_briquetas = db.Column(db.Boolean, default=False)
    fecha_registro = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Auditoría de quién registró

    lote = db.relationship('Lote', backref='mermas')

class Proveedor(db.Model):
    __tablename__ = 'proveedores'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False, unique=True)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    frecuencia_compra_dias = db.Column(db.Integer)  
    ultima_fecha_compra = db.Column(db.DateTime(timezone=True))   

    ventas = db.relationship('Venta', backref='cliente', lazy=True)

    @property
    def saldo_pendiente(self):
        return sum(
            venta.total - sum(pago.monto for pago in venta.pagos)
            for venta in self.ventas
            if venta.estado_pago != 'pagado'
        )

    def __repr__(self):
        return f'<Cliente {self.nombre}>'



class Pago(db.Model):
    __tablename__ = "pagos"
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False) 
    fecha = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    metodo_pago = db.Column(db.String(20), nullable=False)  # "efectivo", "transferencia", "tarjeta"
    referencia = db.Column(db.String(50))  # Número de transacción o comprobante
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Quién registró el pago

    __table_args__ = (
        CheckConstraint("metodo_pago IN ('efectivo', 'transferencia', 'tarjeta')"),
    )

class Movimiento(db.Model):
    __tablename__ = 'movimientos'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False)
    
    # Relación con PresentacionProducto (1)
    presentacion_id = db.Column(db.Integer, db.ForeignKey('presentaciones_producto.id', ondelete='CASCADE'))
    presentacion = db.relationship('PresentacionProducto')
    
    # Relación con Lote (2)
    lote_id = db.Column(db.Integer, db.ForeignKey('lotes.id', ondelete='SET NULL'))
    lote = db.relationship('Lote')
    
    # Relación con Usuario (3)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    usuario = db.relationship('Users', back_populates='movimientos')  # Nombre del modelo en singular
    
    cantidad = db.Column(db.Numeric(12, 2), nullable=False)
    fecha = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    motivo = db.Column(db.String(255))

    __table_args__ = (
        CheckConstraint("tipo IN ('entrada', 'salida')"),
        CheckConstraint("cantidad > 0"),
    )

class Gasto(db.Model):
    __tablename__ = 'gastos'
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text, nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    fecha = db.Column(db.Date, default=lambda: datetime.now(timezone.utc))
    categoria = db.Column(db.String(50), nullable=False)  # "logistica", "personal", "otros"
    almacen_id = db.Column(db.Integer, db.ForeignKey('almacenes.id'))  # Relación con almacén
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Quién registró el gasto

    __table_args__ = (
        CheckConstraint("categoria IN ('logistica', 'personal', 'otros')"),
    )