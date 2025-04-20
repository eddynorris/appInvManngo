# app/api/v1/endpoints/cliente.py (Actualizado)
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any
from app import crud, models, schemas # Importar crud completo
from app.api import deps
from decimal import Decimal # Para saldo pendiente
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Users


router = APIRouter()
@router.get("/", response_model=List[schemas.Cliente])
def read_clientes(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=200),
    current_user: "Users" = Depends(deps.get_current_active_user),
) -> Any:
    """Recupera lista de clientes."""
    clientes = crud.crud_cliente.get_clientes(db, skip=skip, limit=limit)
    # Calcular saldo pendiente para cada cliente
    # Esto puede ser ineficiente para listas grandes, considerar optimizar
    clientes_con_saldo = []
    for cliente in clientes:
        # Asumiendo que tienes una relación 'ventas' y 'pagos' cargada o calculas aquí
        # saldo = crud.crud_cliente.calculate_saldo_pendiente(db, cliente.id) # Opción 1: Función CRUD específica
        saldo = cliente.saldo_pendiente # Opción 2: Usar la @property (si la relación está cargada)
        cliente_schema = schemas.Cliente.model_validate(cliente) # Convertir ORM a Pydantic
        cliente_schema.saldo_pendiente = saldo # Asignar saldo calculado
        clientes_con_saldo.append(cliente_schema)
    # return clientes # Sin cálculo de saldo
    return clientes_con_saldo
@router.post("/", response_model=schemas.Cliente, status_code=status.HTTP_201_CREATED)
def create_cliente(
    *,
    db: Session = Depends(deps.get_db),
    cliente_in: schemas.ClienteCreate,
    current_user: "Users" = Depends(deps.require_rol('admin', 'gerente')), # Ejemplo: Admin o Gerente crean
) -> Any:
    """Crea un nuevo cliente."""
    cliente = crud.crud_cliente.create_cliente(db=db, cliente=cliente_in)
    return cliente
@router.get("/{cliente_id}", response_model=schemas.Cliente)
def read_cliente_by_id(
    cliente_id: int,
    db: Session = Depends(deps.get_db),
    current_user: "Users" = Depends(deps.get_current_active_user),
) -> Any:
    """Obtiene un cliente por ID."""
    cliente = crud.crud_cliente.get_cliente(db, cliente_id=cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    # Calcular saldo pendiente
    saldo = cliente.saldo_pendiente
    cliente_schema = schemas.Cliente.model_validate(cliente)
    cliente_schema.saldo_pendiente = saldo
    return cliente_schema
@router.put("/{cliente_id}", response_model=schemas.Cliente)
def update_cliente(
    *,
    db: Session = Depends(deps.get_db),
    cliente_id: int,
    cliente_in: schemas.ClienteUpdate,
    current_user: "Users" = Depends(deps.require_rol('admin', 'gerente')), # Ejemplo
) -> Any:
    """Actualiza un cliente."""
    cliente = crud.crud_cliente.get_cliente(db, cliente_id=cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    cliente = crud.crud_cliente.update_cliente(db=db, db_obj=cliente, obj_in=cliente_in)
    # Recalcular saldo si es necesario o devolver como en GET
    saldo = cliente.saldo_pendiente
    cliente_schema = schemas.Cliente.model_validate(cliente)
    cliente_schema.saldo_pendiente = saldo
    return cliente_schema
@router.delete("/{cliente_id}", response_model=schemas.Cliente)
def delete_cliente(
    *,
    db: Session = Depends(deps.get_db),
    cliente_id: int,
    current_user: "Users" = Depends(deps.require_admin), # Ejemplo: Solo admin elimina
) -> Any:
    """Elimina un cliente."""
    cliente = crud.crud_cliente.get_cliente(db, cliente_id=cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    # Considerar lógica si tiene ventas/pagos pendientes
    deleted_cliente = crud.crud_cliente.delete_cliente(db=db, cliente_id=cliente_id)
    # No se puede calcular saldo si ya está eliminado
    return deleted_cliente