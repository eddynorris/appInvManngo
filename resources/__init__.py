from .auth_resource import AuthResource
from .producto_resource import ProductoResource
from .almacen_resource import AlmacenResource
from .cliente_resource import ClienteResource
from .gasto_resource import GastoResource
from .movimiento_resource import MovimientoResource
from .venta_resource import VentaResource
from .user_resource import UserResource

__all__ = [
    'AuthResource',
    'UserResource',
    'ProductoResource',
    'AlmacenResource',
    'ClienteResource',
    'GastoResource',
    'MovimientoResource',
    'VentaResource',
    'PagoResource'
]