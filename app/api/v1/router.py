# app/api/v1/router.py
from fastapi import APIRouter

# Importa los routers de tus endpoints
from app.api.v1.endpoints import (
    almacen, auth, cliente, gasto, inventario, lote, merma,
    movimiento, pago, pedido, presentacion, producto, proveedor, user, venta
) # Asegúrate que todos estén aquí

api_router = APIRouter()

# Incluye los routers de los endpoints con un prefijo y etiquetas para la documentación
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(user.router, prefix="/usuarios", tags=["Usuarios"]) # Añadido
api_router.include_router(almacen.router, prefix="/almacenes", tags=["Almacenes"])
api_router.include_router(cliente.router, prefix="/clientes", tags=["Clientes"])
api_router.include_router(proveedor.router, prefix="/proveedores", tags=["Proveedores"]) # Añadido
api_router.include_router(producto.router, prefix="/productos", tags=["Productos"]) # Añadido
api_router.include_router(presentacion.router, prefix="/presentaciones", tags=["Presentaciones"])
api_router.include_router(lote.router, prefix="/lotes", tags=["Lotes"])
api_router.include_router(inventario.router, prefix="/inventarios", tags=["Inventario"])
api_router.include_router(merma.router, prefix="/mermas", tags=["Mermas"])
api_router.include_router(venta.router, prefix="/ventas", tags=["Ventas"])
api_router.include_router(pago.router, prefix="/pagos", tags=["Pagos"])
api_router.include_router(movimiento.router, prefix="/movimientos", tags=["Movimientos"])
api_router.include_router(gasto.router, prefix="/gastos", tags=["Gastos"])
api_router.include_router(pedido.router, prefix="/pedidos", tags=["Pedidos"])