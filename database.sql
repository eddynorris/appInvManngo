-- Database: invManngo

-- DROP DATABASE IF EXISTS "invManngo";

CREATE DATABASE "invManngo"
    WITH
    OWNER = yor
    ENCODING = 'UTF8'
    LC_COLLATE = 'Spanish_Spain.1252'
    LC_CTYPE = 'Spanish_Spain.1252'
    LOCALE_PROVIDER = 'libc'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;

CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password VARCHAR(256) NOT NULL
);

-- Tablas Principales
CREATE TABLE productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    precio_compra NUMERIC(12,2) NOT NULL,
    precio_venta NUMERIC(12,2) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    stock_minimo INTEGER NOT NULL DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE almacenes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    direccion TEXT,
    ciudad VARCHAR(100)
);

CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    telefono VARCHAR(20),
    direccion TEXT,
    saldo_pendiente NUMERIC(12,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ventas (
    id SERIAL PRIMARY KEY,
    cliente_id INT NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total NUMERIC(12,2) NOT NULL,
    tipo_pago VARCHAR(10) CHECK (tipo_pago IN ('contado', 'credito')),
    fecha_vencimiento DATE,
    estado_pago VARCHAR(15) DEFAULT 'pendiente' CHECK (estado_pago IN ('pendiente', 'parcial', 'pagado'))
);

CREATE TABLE movimientos (
    id SERIAL PRIMARY KEY,
    producto_id INT NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    almacen_id INT NOT NULL REFERENCES almacenes(id) ON DELETE CASCADE,
    venta_id INT REFERENCES ventas(id) ON DELETE CASCADE,
    cantidad NUMERIC(12,2) NOT NULL CHECK (cantidad > 0),
    precio_venta NUMERIC(12,2) NOT NULL,  -- Precio histórico
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('entrada', 'salida')),
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE gastos (
    id SERIAL PRIMARY KEY,
    descripcion TEXT NOT NULL,
    monto NUMERIC(12,2) NOT NULL,
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    categoria VARCHAR(50) NOT NULL
);

-- Índices
CREATE INDEX idx_productos_nombre ON productos(nombre);
CREATE INDEX idx_ventas_fecha ON ventas(fecha);
CREATE INDEX idx_clientes_saldo ON clientes(saldo_pendiente);
CREATE INDEX idx_movimientos_venta ON movimientos(venta_id);

-- Triggers y Funciones
CREATE OR REPLACE FUNCTION actualizar_stock()
RETURNS TRIGGER AS $$
DECLARE
    stock_actual NUMERIC;
BEGIN
    IF NEW.tipo = 'entrada' THEN
        UPDATE productos SET stock = stock + NEW.cantidad WHERE id = NEW.producto_id;
    ELSIF NEW.tipo = 'salida' THEN
        SELECT stock INTO stock_actual FROM productos WHERE id = NEW.producto_id;
        
        IF stock_actual < NEW.cantidad THEN
            RAISE EXCEPTION 'Stock insuficiente para el producto ID %', NEW.producto_id;
        END IF;
        
        UPDATE productos SET stock = stock - NEW.cantidad WHERE id = NEW.producto_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION actualizar_saldo_cliente()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.tipo_pago = 'credito' THEN
        UPDATE clientes
        SET saldo_pendiente = saldo_pendiente + NEW.total
        WHERE id = NEW.cliente_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_stock
AFTER INSERT ON movimientos
FOR EACH ROW
EXECUTE FUNCTION actualizar_stock();

CREATE TRIGGER trigger_saldo_cliente
AFTER INSERT ON ventas
FOR EACH ROW
EXECUTE FUNCTION actualizar_saldo_cliente();

-- Vista Materializada para Reportes
CREATE MATERIALIZED VIEW ventas_mensuales AS
SELECT
    m.almacen_id,
    DATE_TRUNC('month', v.fecha) AS mes,
    SUM(m.cantidad * m.precio_venta) AS total_ventas,
    AVG(m.cantidad * m.precio_venta) AS promedio_diario
FROM ventas v
JOIN movimientos m ON v.id = m.venta_id
GROUP BY m.almacen_id, DATE_TRUNC('month', v.fecha);

-- Optimizaciones Adicionales
COMMENT ON TABLE productos IS 'Almacena información de productos con stock mínimo';
COMMENT ON COLUMN movimientos.precio_venta IS 'Precio en el momento de la transacción para auditoría histórica';

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
