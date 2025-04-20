# app/api/v1/endpoints/merma.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any
from app import crud, models, schemas, services
from app.api import deps
import logging
logger = logging.getLogger(__name__)
router = APIRouter()
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Users


@router.get("/", response_model=List[schemas.Merma])
def read_mermas(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=200),
    lote_id: int | None = Query(default=None, description="Filtrar por ID de lote"),
    current_user: "Users" = Depends(deps.get_current_active_user),
) -> Any:
    """Recupera lista de mermas."""
    # Añadir lógica de autorización si es necesario (ej: solo ver mermas de tu almacén)
    mermas = crud.crud_merma.get_mermas(db, skip=skip, limit=limit, lote_id=lote_id)
    return mermas

@router.post("/", response_model=schemas.Merma, status_code=status.HTTP_201_CREATED)
def create_merma(
    *,
    db: Session = Depends(deps.get_db),
    merma_in: schemas.MermaCreate,
    current_user: "Users" = Depends(deps.get_current_active_user), # Quién registra
) -> Any:
    """Registra una merma y actualiza la cantidad del lote."""
    # Verificar si el usuario puede registrar mermas para este lote/almacén?
    lote = crud.crud_lote.get_lote(db, merma_in.lote_id)
    if not lote:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Lote ID {merma_in.lote_id} no encontrado.")
    # Aquí podrías verificar si el lote pertenece a un almacén al que el usuario tiene acceso

    try:
        merma = services.service_merma.create_merma_and_update_lote(
            db=db, merma=merma_in, current_user_id=current_user.id
        )
        return merma
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error inesperado en create_merma endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al crear la merma.")

@router.get("/{merma_id}", response_model=schemas.Merma)
def read_merma_by_id(
    merma_id: int,
    db: Session = Depends(deps.get_db),
    current_user: "Users" = Depends(deps.get_current_active_user),
) -> Any:
    """Obtiene una merma por ID."""
    merma = crud.crud_merma.get_merma(db, merma_id=merma_id)
    if not merma:
        raise HTTPException(status_code=404, detail="Merma no encontrada")
    # Añadir lógica de autorización si es necesario
    return merma

# PUT y DELETE para Merma son menos comunes, pero si los necesitas:
# - PUT podría usar crud_merma.update_merma_simple para cambiar 'convertido_a_briquetas'.
# - DELETE debería llamar a un service_merma.delete_merma_and_restore_lote si se necesita revertir.