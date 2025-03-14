-- Database: invManngo

-- DROP DATABASE IF EXISTS "invManngo";


CREATE DATABASE "manngo_db"
    WITH
    OWNER = yor
    ENCODING = 'UTF8'
    LC_COLLATE = 'Spanish_Spain.1252'
    LC_CTYPE = 'Spanish_Spain.1252'
    LOCALE_PROVIDER = 'libc'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;

CREATE TABLE almacenes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    direccion TEXT,
    ciudad VARCHAR(100)
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password VARCHAR(256) NOT NULL,
    rol VARCHAR(20) NOT NULL DEFAULT 'usuario',
    almacen_id INTEGER REFERENCES almacenes(id) ON DELETE SET NULL
);

CREATE TABLE productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) UNIQUE NOT NULL,
    descripcion TEXT,
    precio_compra NUMERIC(12,2) NOT NULL,
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE presentaciones_producto (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL,
    capacidad_kg NUMERIC(10,2) NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('bruto', 'procesado', 'merma', 'briqueta', 'detalle')),
    precio_venta NUMERIC(12,2) NOT NULL,
    activo BOOLEAN DEFAULT true,
    UNIQUE (producto_id, nombre)
);
CREATE INDEX idx_presentaciones_tipo ON presentaciones_producto(tipo);

CREATE TABLE proveedores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    direccion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lotes (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    proveedor_id INTEGER REFERENCES proveedores(id) ON DELETE SET NULL,
    peso_humedo_kg NUMERIC(10,2) NOT NULL,
    peso_seco_kg NUMERIC(10,2),
    fecha_ingreso TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    telefono VARCHAR(20),
    direccion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    frecuencia_compra_dias INTEGER,
    ultima_fecha_compra TIMESTAMP
);

CREATE TABLE inventario (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    presentacion_id INTEGER NOT NULL REFERENCES presentaciones_producto(id) ON DELETE CASCADE,
    almacen_id INTEGER NOT NULL REFERENCES almacenes(id) ON DELETE CASCADE,
    lote_id INTEGER REFERENCES lotes(id) ON DELETE SET NULL,
    cantidad INTEGER NOT NULL DEFAULT 0 CHECK (cantidad >= 0),
    stock_minimo INTEGER NOT NULL DEFAULT 10,
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (producto_id, presentacion_id, almacen_id)
);
CREATE INDEX idx_inventario_almacen ON inventario(almacen_id, presentacion_id);

CREATE TABLE ventas (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    almacen_id INTEGER NOT NULL REFERENCES almacenes(id) ON DELETE CASCADE,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total NUMERIC(12,2) NOT NULL CHECK (total > 0),
    tipo_pago VARCHAR(10) NOT NULL CHECK (tipo_pago IN ('contado', 'credito')),
    estado_pago VARCHAR(15) DEFAULT 'pendiente' CHECK (estado_pago IN ('pendiente', 'parcial', 'pagado')),
    consumo_diario_kg NUMERIC(10,2)
);

CREATE TABLE venta_detalles (
    id SERIAL PRIMARY KEY,
    venta_id INTEGER NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
    presentacion_id INTEGER NOT NULL REFERENCES presentaciones_producto(id) ON DELETE CASCADE,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(12,2) NOT NULL
);

CREATE TABLE mermas (
    id SERIAL PRIMARY KEY,
    lote_id INTEGER NOT NULL REFERENCES lotes(id) ON DELETE CASCADE,
    cantidad_kg NUMERIC(10,2) NOT NULL CHECK (cantidad_kg > 0),
    convertido_a_briquetas BOOLEAN DEFAULT false,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pagos (
    id SERIAL PRIMARY KEY,
    venta_id INTEGER NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
    monto NUMERIC(12,2) NOT NULL CHECK (monto > 0),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metodo_pago VARCHAR(20) NOT NULL CHECK (metodo_pago IN ('efectivo', 'transferencia', 'tarjeta')),
    referencia VARCHAR(50),
    usuario_id INTEGER REFERENCES users(id)
);

CREATE TABLE movimientos (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('entrada', 'salida')),
    presentacion_id INTEGER NOT NULL REFERENCES presentaciones_producto(id) ON DELETE CASCADE,
    lote_id INTEGER REFERENCES lotes(id) ON DELETE SET NULL,
    usuario_id INTEGER REFERENCES users(id),
    cantidad NUMERIC(12,2) NOT NULL CHECK (cantidad > 0),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    motivo VARCHAR(255)
);

CREATE TABLE gastos (
    id SERIAL PRIMARY KEY,
    descripcion TEXT NOT NULL,
    monto NUMERIC(12,2) NOT NULL CHECK (monto > 0),
    fecha DATE DEFAULT CURRENT_DATE,
    categoria VARCHAR(50) NOT NULL CHECK (categoria IN ('logistica', 'personal', 'otros')),
    almacen_id INTEGER REFERENCES almacenes(id),
    usuario_id INTEGER REFERENCES users(id)
);

CREATE TABLE pedidos (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    almacen_id INTEGER NOT NULL REFERENCES almacenes(id) ON DELETE CASCADE,
    vendedor_id INTEGER REFERENCES users(id),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_entrega TIMESTAMP NOT NULL,
    estado VARCHAR(20) DEFAULT 'programado' CHECK (estado IN ('programado', 'confirmado', 'entregado', 'cancelado')),
    notas TEXT
);

CREATE TABLE pedido_detalles (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    presentacion_id INTEGER NOT NULL REFERENCES presentaciones_producto(id) ON DELETE CASCADE,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_estimado NUMERIC(12,2) NOT NULL
);

-- Insertar datos de productos
INSERT INTO productos (nombre, descripcion, precio_compra, precio_venta, stock, stock_minimo) VALUES
('Saco de 30kg', 'Saco de carbon vegetal en presentacion de 30kg', 42, 87, 0),
('Saco 20 kg', 'Saco de carbon vegetal en presentacion de 20kg',29, 58, 0),
('Bolsa de 10kg', 'Bolsa de papel con carbon vegetal en presentacion de 10kg',15, 30, 100),
('Saco de 5kg', 'Saco pequeño de carbon vegetal en presentacion de 5kg',7, 15, 0),
('Bolsa de carbon BioBrasa 5kg', 'Bolsa de carbon para tiendas verde Biobrasa de 5kg',12, 22, 0),
('Bolsa de briquetas Fogo de 4kg', 'Briquetas de carbon vegetal rojo fogo de chao de 4kg', 8, 16.5, 0),
('Bolsa de carbon Fogo 3k', 'Bolsa de carbon vegetal rojo Fogo de chao de 3kg', 7, 14, 0);

-- Insertar almacenes
INSERT INTO almacenes (nombre, direccion, ciudad) VALUES
('Planta', 'Km 384 Colcabamba', 'Calicocha'),
('Almacen Abancay', 'Av. Tamburco', 'Abancay'),
('Almacen Andahuaylas', 'Av. Peru', 'Anahuaylas');

-- Insertar clientes (con datos de última compra y días para reorden)
INSERT INTO clientes (nombre, telefono, direccion, saldo_pendiente) VALUES
('Pollo Loko', '+51987654321', 'Av. Principal 123', 0,0),
('Polleria Mauris', '+51987654322', 'Calle Los Olivos 456', 0,0),
('Polleria Ricas Brasas', '+51987654323', 'Jr. Libertad 789', 0,0),
('Mateus Restaurant', '+51987654324', 'Av. Sol 101', 0,0),
('Carboleña del Olivo', '+51987654325', 'Calle Paz 202', 0,0),
('Polleria La Fogata', '+51987654326', 'Av. Luna 303', 0,0),
('Maria Mayorista', '+51987654327', 'Jr. Estrella 404', 0,0),
('Dcarmen', '+51987654328', 'Av. Marte 505', 0,0),
('Polleria Gael', '+51987654329', 'Calle Tierra 606', 0,0);
