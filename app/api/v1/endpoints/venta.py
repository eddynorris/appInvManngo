# app/api/v1/endpoints/venta.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional
from datetime import date, datetime # Para filtros de fecha
from app import crud, models, schemas, services
from app.api import deps
import logging
from decimal import Decimal # Para saldo pendiente
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Users

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[schemas.Venta])
def read_ventas(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=200),
    cliente_id: int | None = Query(default=None),
    almacen_id: int | None = Query(default=None),
    vendedor_id: int | None = Query(default=None),
    estado_pago: str | None = Query(default=None, pattern="^(pendiente|parcial|pagado)$"),
    fecha_inicio: Optional[date] = Query(default=None, description="Formato YYYY-MM-DD"),
    fecha_fin: Optional[date] = Query(default=None, description="Formato YYYY-MM-DD"),
    current_user: "Users" = Depends(deps.get_current_active_user),
) -> Any:
    """Recupera lista de ventas con filtros opcionales."""
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
        "estado_pago": estado_pago,
        # Convertir date a datetime para el filtro between si es necesario
        "fecha_inicio": datetime.combine(fecha_inicio, datetime.min.time()) if fecha_inicio else None,
        "fecha_fin": datetime.combine(fecha_fin, datetime.max.time()) if fecha_fin else None,
    }
    active_filters = {k: v for k, v in filters.items() if v is not None}

    ventas = crud.crud_venta.get_ventas(db, skip=skip, limit=limit, **active_filters)
    # Calcular saldo pendiente
    ventas_con_saldo = []
    for venta in ventas:
         # saldo = venta.saldo_pendiente # Usar property si está cargada
         saldo = venta.total - sum(p.monto for p in venta.pagos)
         venta_schema = schemas.Venta.model_validate(venta)
         venta_schema.saldo_pendiente = saldo
         ventas_con_saldo.append(venta_schema)
    return ventas_con_saldo

@router.post("/", response_model=schemas.Venta, status_code=status.HTTP_201_CREATED)
def create_venta(
    *,
    db: Session = Depends(deps.get_db),
    venta_in: schemas.VentaCreate,
    current_user: "Users" = Depends(deps.get_current_active_user), # Vendedor
) -> Any:
    """Crea una nueva venta, actualiza inventario y crea movimientos."""
    # Verificar permiso de almacén
    if current_user.rol != 'admin' and venta_in.almacen_id != current_user.almacen_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permiso para crear ventas en este almacén.")

    try:
        venta = services.service_venta.create_venta_with_details(
            db=db, venta_in=venta_in, vendedor_id=current_user.id
        )
        return venta
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error inesperado en create_venta endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al crear la venta.")


@router.get("/{venta_id}", response_model=schemas.Venta)
def read_venta_by_id(
    venta_id: int,
    db: Session = Depends(deps.get_db),
    current_user: "Users" = Depends(deps.get_current_active_user),
) -> Any:
    """Obtiene una venta por ID."""
    venta = crud.crud_venta.get_venta(db, venta_id=venta_id)
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    # Verificar permiso de almacén
    deps.get_verified_almacen(venta.almacen_id, current_user)
    # Calcular saldo
    saldo = venta.total - sum(p.monto for p in venta.pagos)
    venta_schema = schemas.Venta.model_validate(venta)
    venta_schema.saldo_pendiente = saldo
    return venta_schema

@router.put("/{venta_id}", response_model=schemas.Venta)
def update_venta(
    *,
    db: Session = Depends(deps.get_db),
    venta_id: int,
    venta_in: schemas.VentaUpdate,
    current_user: "Users" = Depends(deps.require_rol('admin', 'gerente')), # Ejemplo
) -> Any:
    """Actualiza campos simples de una venta (tipo/estado pago, consumo)."""
    venta = crud.crud_venta.get_venta(db, venta_id=venta_id)
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    # Verificar permiso de almacén
    deps.get_verified_almacen(venta.almacen_id, current_user)
    updated_venta = crud.crud_venta.update_venta_simple(db=db, db_obj=venta, obj_in=venta_in)
    # Recalcular saldo si es necesario
    saldo = updated_venta.total - sum(p.monto for p in updated_venta.pagos)
    venta_schema = schemas.Venta.model_validate(updated_venta)
    venta_schema.saldo_pendiente = saldo
    return venta_schema


@router.delete("/{venta_id}", response_model=schemas.Venta)
def delete_venta(
    *,
    db: Session = Depends(deps.get_db),
    venta_id: int,
    current_user: "Users" = Depends(deps.require_admin), # Ejemplo: Solo admin elimina ventas
) -> Any:
    """Elimina una venta y revierte inventario/movimientos."""
    venta = crud.crud_venta.get_venta(db, venta_id=venta_id)
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
     # Verificar permiso de almacén
    deps.get_verified_almacen(venta.almacen_id, current_user)

    try:
        deleted_venta = services.service_venta.delete_venta_and_reverse(
            db=db, venta_id=venta_id, current_user_id=current_user.id
        )
        return deleted_venta # Devuelve el objeto eliminado
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error inesperado en delete_venta endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al eliminar la venta.")
