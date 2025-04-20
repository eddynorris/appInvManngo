# app/schemas/__init__.py
# Importa todos los esquemas Pydantic principales para fácil acceso
from .schema_almacen import Almacen, AlmacenCreate, AlmacenUpdate
from .schema_user import User, UserCreate, UserUpdate, UserLogin
from .schema_proveedor import Proveedor, ProveedorCreate, ProveedorUpdate
from .schema_producto import Producto, ProductoCreate, ProductoUpdate
from .schema_presentacion import Presentacion, PresentacionCreate, PresentacionUpdate
from .schema_lote import Lote, LoteCreate, LoteUpdate
from .schema_merma import Merma, MermaCreate, MermaUpdate
from .schema_inventario import Inventario, InventarioCreate, InventarioUpdate
from .schema_cliente import Cliente, ClienteCreate, ClienteUpdate
from .schema_movimiento import Movimiento, MovimientoCreate
from .schema_venta_detalle import VentaDetalle, VentaDetalleCreate, VentaDetalleUpdate
from .schema_venta import Venta, VentaCreate, VentaUpdate
from .schema_pago import Pago, PagoCreate, PagoUpdate
from .schema_gasto import Gasto, GastoCreate, GastoUpdate
from .schema_pedido_detalle import PedidoDetalle, PedidoDetalleCreate, PedidoDetalleUpdate
from .schema_pedido import Pedido, PedidoCreate, PedidoUpdate

# Importar Schemas de Token
from .schema_token import Token, TokenPayload

# Puedes eliminar el archivo schemas_marshmallow.py si ya no lo necesitas
# o mantenerlo como referencia