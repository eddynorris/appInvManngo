# app/api/v1/endpoints/pago.py
from fastapi import (
    APIRouter, Depends, HTTPException, status, Query,
    UploadFile, File, Form # <--- Necesario para archivos
)
from sqlalchemy.orm import Session
from typing import List, Any, Optional
from decimal import Decimal # Importar Decimal
from app import crud, models, schemas, services
from app.api import deps
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Users


logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[schemas.Pago])
def read_pagos(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=200),
    venta_id: int | None = Query(default=None, description="Filtrar pagos por ID de venta"),
    current_user: "Users" = Depends(deps.get_current_active_user),
) -> Any:
    """Recupera lista de pagos, opcionalmente filtrados por venta."""
    # TODO: Añadir lógica de autorización si es necesario (ej: solo ver pagos de tus ventas/almacén)
    # Por ejemplo, verificar que el usuario tenga acceso al almacén de la venta si venta_id se proporciona.
    pagos = crud.crud_pago.get_pagos(db, skip=skip, limit=limit, venta_id=venta_id)
    return pagos

# Usar async def por el manejo de archivos
@router.post("/", response_model=schemas.Pago, status_code=status.HTTP_201_CREATED)
async def create_pago( # <--- async def
    *,
    db: Session = Depends(deps.get_db),
    # Recibir datos como Formulario debido al archivo
    venta_id: int = Form(...),
    monto: float = Form(...), # Recibir como float, Pydantic/SQLAlchemy maneja Decimal
    metodo_pago: str = Form(...),
    referencia: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None, description="Comprobante de pago (opcional)"),
    current_user: "Users" = Depends(deps.get_current_active_user), # Quién registra el pago
) -> Any:
    """
    Registra un nuevo pago, sube comprobante opcionalmente, y actualiza el estado de la venta.
    """
    # Verificar si la venta existe y si el usuario tiene permiso sobre su almacén
    venta = crud.crud_venta.get_venta(db, venta_id)
    if not venta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Venta ID {venta_id} no encontrada.")
    try:
        deps.get_verified_almacen(venta.almacen_id, current_user)
    except HTTPException as auth_exc:
        logger.warning(f"Intento no autorizado de registrar pago para venta {venta_id} por usuario {current_user.id}")
        raise auth_exc # Re-lanzar 403

    file_url = None
    if file:
        file_url = await save_upload_file(upload_file=file, destination_folder="comprobantes")
        if not file_url:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo guardar el comprobante.")

    pago_in = schemas.PagoCreate(
        venta_id=venta_id,
        monto=Decimal(str(monto)), # Convertir float a Decimal de forma segura
        metodo_pago=metodo_pago,
        referencia=referencia,
        url_comprobante=file_url
        # usuario_id se asigna en el servicio
    )

    try:
        pago = services.service_pago.create_pago_and_update_venta(
            db=db, pago_in=pago_in, usuario_id=current_user.id
        )
        return pago
    except HTTPException as http_exc:
        # Si el servicio lanza HTTPException (ej: error interno), relanzar
        raise http_exc
    except Exception as e:
        # Capturar otros errores inesperados (aunque el servicio debería manejarlos)
        logger.error(f"Error inesperado en create_pago endpoint (Venta ID {venta_id}): {e}", exc_info=True)
        # Borrar archivo subido si la operación falló después de subirlo
        if file_url:
            delete_file(file_url)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al crear el pago.")


@router.get("/{pago_id}", response_model=schemas.Pago)
def read_pago_by_id(
    pago_id: int,
    db: Session = Depends(deps.get_db),
    current_user: "Users" = Depends(deps.get_current_active_user),
) -> Any:
    """Obtiene un pago por ID."""
    pago = crud.crud_pago.get_pago(db, pago_id=pago_id)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    # Verificar permiso sobre el almacén de la venta asociada
    deps.get_verified_almacen(pago.venta.almacen_id, current_user)
    return pago

# Usar async def por el manejo de archivos
@router.put("/{pago_id}", response_model=schemas.Pago)
async def update_pago( # <--- async def
    *,
    db: Session = Depends(deps.get_db),
    pago_id: int,
    # Recibir datos como Formulario
    referencia: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None, description="Nuevo comprobante (reemplaza el anterior si existe)"),
    current_user: "Users" = Depends(deps.require_rol('admin', 'gerente')), # Ejemplo
) -> Any:
    """
    Actualiza campos simples de un pago (referencia, url_comprobante).
    Reemplaza el comprobante si se sube uno nuevo.
    """
    pago = crud.crud_pago.get_pago(db, pago_id=pago_id)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    # Verificar permiso sobre el almacén de la venta asociada
    deps.get_verified_almacen(pago.venta.almacen_id, current_user)

    old_file_url = pago.url_comprobante
    file_url = old_file_url # Mantener por defecto

    if file:
        file_url = await save_upload_file(upload_file=file, destination_folder="comprobantes")
        if not file_url:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo guardar el nuevo comprobante.")
        if old_file_url and old_file_url != file_url:
             delete_file(old_file_url) # Borrar antiguo si se subió uno nuevo

    # Crear el objeto de actualización Pydantic
    pago_in = schemas.PagoUpdate(
        referencia=referencia,
        url_comprobante=file_url # Actualizar con la nueva URL (o la antigua si no cambió)
    )

    # Llamar al CRUD simple para actualizar
    updated_pago = crud.crud_pago.update_pago_simple(db=db, db_obj=pago, obj_in=pago_in)
    return updated_pago

@router.delete("/{pago_id}", response_model=schemas.Pago)
def delete_pago(
    *,
    db: Session = Depends(deps.get_db),
    pago_id: int,
    current_user: "Users" = Depends(deps.require_admin), # Ejemplo: Solo admin elimina pagos
) -> Any:
    """Elimina un pago, su comprobante asociado, y actualiza el estado de la venta."""
    pago = crud.crud_pago.get_pago(db, pago_id=pago_id)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    # Verificar permiso sobre el almacén de la venta asociada
    deps.get_verified_almacen(pago.venta.almacen_id, current_user)

    file_to_delete = pago.url_comprobante # Guardar URL antes de llamar al servicio

    try:
        deleted_pago = services.service_pago.delete_pago_and_update_venta(db=db, pago_id=pago_id)
        # Si la operación de BD fue exitosa, eliminar archivo
        if file_to_delete:
            delete_file(file_to_delete)
        return deleted_pago # Devuelve el objeto eliminado
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error inesperado en delete_pago endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al eliminar el pago.")