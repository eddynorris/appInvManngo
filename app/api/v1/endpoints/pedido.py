# app/api/v1/endpoints/pedido.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any
from app import crud, models, schemas, services # Importar services
from app.api import deps
import logging
from decimal import Decimal # Para total estimado
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Users


logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[schemas.Pedido])
def read_pedidos(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=200),
    cliente_id: int | None = Query(default=None),
    almacen_id: int | None = Query(default=None),
    vendedor_id: int | None = Query(default=None),
    estado: str | None = Query(default=None),
    # Añadir filtros de fecha si es necesario
    current_user: "Users" = Depends(deps.get_current_active_user),
) -> Any:
    """Recupera lista de pedidos con filtros opcionales."""
    # Aplicar filtro de almacén si el usuario no es admin
    query_almacen_id = almacen_id
    if current_user.rol != 'admin':
        if query_almacen_id is None:
            query_almacen_id = current_user.almacen_id
        elif query_almacen_id != current_user.almacen_id:
             return [] # O 403

    filters = {
        "cliente_id": cliente_id,
        "almacen_id": query_almacen_id,
        "vendedor_id": vendedor_id,
        "estado": estado,
    }
    # Eliminar filtros nulos
    active_filters = {k: v for k, v in filters.items() if v is not None}

    pedidos = crud.crud_pedido.get_pedidos(db, skip=skip, limit=limit, **active_filters)
    # Calcular total estimado para cada pedido
    pedidos_con_total = []
    for pedido in pedidos:
        # total_estimado = pedido.total_estimado # Si la @property funciona con relaciones cargadas
        total_estimado = sum(d.cantidad * d.precio_estimado for d in pedido.detalles)
        pedido_schema = schemas.Pedido.model_validate(pedido)
        pedido_schema.total_estimado = total_estimado
        pedidos_con_total.append(pedido_schema)
    return pedidos_con_total


@router.post("/", response_model=schemas.Pedido, status_code=status.HTTP_201_CREATED)
def create_pedido(
    *,
    db: Session = Depends(deps.get_db),
    pedido_in: schemas.PedidoCreate,
    current_user: "Users" = Depends(deps.get_current_active_user), # Quién crea
) -> Any:
    """Crea un nuevo pedido."""
    # Verificar permiso de almacén
    if current_user.rol != 'admin' and pedido_in.almacen_id != current_user.almacen_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permiso para crear pedidos en este almacén.")

    try:
        # Usar CRUD simple, commit se hace aquí porque la operación es autocontenida por ahora
        db_pedido = crud.crud_pedido.create_pedido_simple(db=db, pedido_in=pedido_in, vendedor_id=current_user.id)
        db.commit()
        db.refresh(db_pedido)
        return db_pedido
    except ValueError as ve: # Capturar errores de validación de create_pedido_simple
         db.rollback()
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado en create_pedido endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al crear el pedido.")


@router.get("/{pedido_id}", response_model=schemas.Pedido)
def read_pedido_by_id(
    pedido_id: int,
    db: Session = Depends(deps.get_db),
    current_user: "Users" = Depends(deps.get_current_active_user),
) -> Any:
    """Obtiene un pedido por ID."""
    pedido = crud.crud_pedido.get_pedido(db, pedido_id=pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    # Verificar permiso de almacén
    deps.get_verified_almacen(pedido.almacen_id, current_user)
    # Calcular total
    total_estimado = sum(d.cantidad * d.precio_estimado for d in pedido.detalles)
    pedido_schema = schemas.Pedido.model_validate(pedido)
    pedido_schema.total_estimado = total_estimado
    return pedido_schema


@router.put("/{pedido_id}", response_model=schemas.Pedido)
def update_pedido(
    *,
    db: Session = Depends(deps.get_db),
    pedido_id: int,
    pedido_in: schemas.PedidoUpdate,
    current_user: "Users" = Depends(deps.get_current_active_user), # O rol específico
) -> Any:
    """Actualiza campos simples de un pedido (estado, fecha entrega, notas)."""
    pedido = crud.crud_pedido.get_pedido(db, pedido_id=pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    # Verificar permiso de almacén
    deps.get_verified_almacen(pedido.almacen_id, current_user)
    updated_pedido = crud.crud_pedido.update_pedido_simple(db=db, db_obj=pedido, obj_in=pedido_in)
    # Recalcular total si es necesario (aunque no debería cambiar con campos simples)
    return updated_pedido


@router.delete("/{pedido_id}", response_model=schemas.Pedido)
def delete_pedido(
    *,
    db: Session = Depends(deps.get_db),
    pedido_id: int,
    current_user: "Users" = Depends(deps.require_rol('admin', 'gerente')), # Ejemplo
) -> Any:
    """Elimina un pedido."""
    pedido = crud.crud_pedido.get_pedido(db, pedido_id=pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    # Verificar permiso de almacén
    deps.get_verified_almacen(pedido.almacen_id, current_user)
    deleted_pedido = crud.crud_pedido.delete_pedido_simple(db=db, pedido_id=pedido_id)
    return deleted_pedido

# Endpoint para convertir Pedido a Venta
@router.post("/{pedido_id}/convertir", response_model=schemas.Venta)
def convert_pedido(
    *,
    db: Session = Depends(deps.get_db),
    pedido_id: int,
    current_user: "Users" = Depends(deps.get_current_active_user), # O rol específico
) -> Any:
    """Convierte un pedido confirmado en una venta."""
    pedido = crud.crud_pedido.get_pedido(db, pedido_id=pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    # Verificar permiso de almacén
    deps.get_verified_almacen(pedido.almacen_id, current_user)

    try:
        venta = services.service_pedido.convert_pedido_to_venta(
            db=db, pedido_id=pedido_id, current_user_id=current_user.id
        )
        return venta
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error inesperado en convert_pedido endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al convertir el pedido.")
