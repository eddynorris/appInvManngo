# app/api/v1/endpoints/inventario.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any
from app import crud, models, schemas, services
from app.api import deps
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Users
    from app.models.models import Inventario

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[schemas.Inventario])
def read_inventarios(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=200),
    almacen_id: int | None = Query(default=None, description="Filtrar por ID de almacén"),
    # Añadir más filtros si son necesarios (ej: presentacion_id)
    current_user: "Users" = Depends(deps.get_current_active_user),
) -> Any:
    """Recupera lista de registros de inventario."""
    # Aplicar filtro de almacén si el usuario no es admin
    if current_user.rol != 'admin':
        if almacen_id is None:
            almacen_id = current_user.almacen_id # Ver solo su almacén por defecto
        elif almacen_id != current_user.almacen_id:
             # Si intenta ver otro almacén, devolver lista vacía o error 403
             # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permiso para ver este almacén.")
             return [] # Opcionalmente devuelve vacío

    inventarios = crud.crud_inventario.get_inventarios(db, skip=skip, limit=limit, almacen_id=almacen_id)
    return inventarios

@router.post("/", response_model=schemas.Inventario, status_code=status.HTTP_201_CREATED)
def create_inventario_entry(
    *,
    db: Session = Depends(deps.get_db),
    inventario_in: schemas.InventarioCreate,
    current_user: "Users" = Depends(deps.require_rol('admin', 'gerente')), # Ejemplo
) -> Any:
    """
    Crea una nueva entrada de inventario.
    Nota: Esto crea solo el registro. Para ajustar stock con movimiento, usar PUT o un servicio específico.
    """
    # Verificar permiso de almacén
    if current_user.rol != 'admin' and inventario_in.almacen_id != current_user.almacen_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permiso para crear inventario en este almacén.")

    # Verificar si ya existe entrada para esta presentación/almacén
    existing = crud.crud_inventario.get_inventario_by_presentacion_almacen(
        db, presentacion_id=inventario_in.presentacion_id, almacen_id=inventario_in.almacen_id
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un registro de inventario para esta presentación en este almacén.")

    # Considerar llamar a un servicio que cree registro Y movimiento inicial?
    inventario = crud.crud_inventario.create_inventario_simple(db=db, inventario=inventario_in)
    return inventario


@router.get("/{inventario_id}", response_model=schemas.Inventario)
def read_inventario_by_id(
    inventario_id: int,
    db: Session = Depends(deps.get_db),
    current_user: "Users" = Depends(deps.get_current_active_user),
) -> Any:
    """Obtiene un registro de inventario por ID."""
    inventario = crud.crud_inventario.get_inventario(db, inventario_id=inventario_id)
    if not inventario:
        raise HTTPException(status_code=404, detail="Inventario no encontrado")
    # Verificar permiso de almacén
    deps.get_verified_almacen(inventario.almacen_id, current_user)
    return inventario

@router.put("/{inventario_id}", response_model=schemas.Inventario)
def update_inventario_entry(
    *,
    db: Session = Depends(deps.get_db),
    inventario_id: int,
    inventario_in: schemas.InventarioUpdate,
    current_user: "Users" = Depends(deps.require_rol('admin', 'gerente')), # Ejemplo
) -> Any:
    """
    Actualiza un registro de inventario.
    Si cambia la cantidad, crea un movimiento de ajuste.
    """
    inventario = crud.crud_inventario.get_inventario(db, inventario_id=inventario_id)
    if not inventario:
        raise HTTPException(status_code=404, detail="Inventario no encontrado")
    # Verificar permiso de almacén
    deps.get_verified_almacen(inventario.almacen_id, current_user)

    try:
        updated_inventario = services.service_inventario.update_inventario_with_adjustment(
            db=db, inventario_id=inventario_id, obj_in=inventario_in, current_user_id=current_user.id
        )
        return updated_inventario
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error inesperado en update_inventario_entry endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al actualizar el inventario.")


@router.delete("/{inventario_id}", response_model=schemas.Inventario)
def delete_inventario_entry(
    *,
    db: Session = Depends(deps.get_db),
    inventario_id: int,
    current_user: "Users" = Depends(deps.require_admin), # Ejemplo: Solo admin elimina registros
) -> Any:
    """
    Elimina un registro de inventario.
    Si había cantidad > 0, crea un movimiento de ajuste de salida.
    """
    inventario = crud.crud_inventario.get_inventario(db, inventario_id=inventario_id)
    if not inventario:
        raise HTTPException(status_code=404, detail="Inventario no encontrado")
    # Verificar permiso de almacén
    deps.get_verified_almacen(inventario.almacen_id, current_user)

    try:
        deleted_inventario = services.service_inventario.delete_inventario_with_adjustment(
            db=db, inventario_id=inventario_id, current_user_id=current_user.id
        )
        return deleted_inventario # Devuelve el objeto eliminado
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error inesperado en delete_inventario_entry endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al eliminar el inventario.")
