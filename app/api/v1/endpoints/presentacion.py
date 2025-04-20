# app/api/v1/endpoints/presentacion.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Any, Optional
from app import crud, models, schemas
from app.api import deps
# Importar utilidad de manejo de archivos
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.models import Users


from app.utils import file_handling # <--- CAMBIO DE IMPORTACIÓN
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[schemas.Presentacion])
def read_presentaciones(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=200),
    producto_id: int | None = Query(default=None),
    activo: bool | None = Query(default=None),
    current_user: "Users" = Depends(deps.get_current_active_user), # Acceso público?
) -> Any:
    """Recupera lista de presentaciones."""
    presentaciones = crud.crud_presentacion.get_presentaciones(
        db, skip=skip, limit=limit, producto_id=producto_id, activo=activo
    )
    return presentaciones

# Cambiar a async def para poder usar await con save_upload_file
@router.post("/", response_model=schemas.Presentacion, status_code=status.HTTP_201_CREATED)
async def create_presentacion( # <--- async def
    *,
    db: Session = Depends(deps.get_db),
    # Recibir datos del formulario y archivo
    nombre: str = Form(...),
    capacidad_kg: float = Form(...),
    tipo: str = Form(...),
    precio_venta: float = Form(...),
    activo: bool = Form(True),
    producto_id: int = Form(...),
    file: Optional[UploadFile] = File(None, description="Archivo de foto (opcional)"),
    current_user: "Users" = Depends(deps.require_rol('admin', 'gerente')), # Ejemplo
) -> Any:
    """Crea una nueva presentación, opcionalmente subiendo una foto."""
    if not crud.crud_producto.get_producto(db, producto_id):
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Producto ID {producto_id} no encontrado.")

    file_url = None
    if file:
        # Guardar archivo y obtener URL/path
        file_url = await save_upload_file(upload_file=file, destination_folder="presentaciones") # <--- Usar await
        if not file_url: # Manejar caso de error en subida
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo guardar la imagen.")


    presentacion_in = schemas.PresentacionCreate(
        nombre=nombre,
        capacidad_kg=capacidad_kg, # Pydantic convertirá float a Decimal si el schema lo especifica
        tipo=tipo,
        precio_venta=precio_venta, # Pydantic convertirá float a Decimal
        activo=activo,
        producto_id=producto_id,
        url_foto=file_url
    )
    presentacion = crud.crud_presentacion.create_presentacion(db=db, presentacion=presentacion_in)
    return presentacion


@router.get("/{presentacion_id}", response_model=schemas.Presentacion)
def read_presentacion_by_id(
    presentacion_id: int,
    db: Session = Depends(deps.get_db),
    current_user: "Users" = Depends(deps.get_current_active_user), # Acceso público?
) -> Any:
    """Obtiene una presentación por ID."""
    presentacion = crud.crud_presentacion.get_presentacion(db, presentacion_id=presentacion_id)
    if not presentacion:
        raise HTTPException(status_code=404, detail="Presentación no encontrada")
    return presentacion

# Cambiar a async def para poder usar await con save_upload_file
@router.put("/{presentacion_id}", response_model=schemas.Presentacion)
async def update_presentacion( # <--- async def
    *,
    db: Session = Depends(deps.get_db),
    presentacion_id: int,
    # Datos pueden venir como Form si hay archivo, o JSON si no
    nombre: Optional[str] = Form(None),
    capacidad_kg: Optional[float] = Form(None),
    tipo: Optional[str] = Form(None),
    precio_venta: Optional[float] = Form(None),
    activo: Optional[bool] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: "Users" = Depends(deps.require_rol('admin', 'gerente')), # Ejemplo
) -> Any:
    """Actualiza una presentación, opcionalmente subiendo/cambiando la foto."""
    presentacion = crud.crud_presentacion.get_presentacion(db, presentacion_id=presentacion_id)
    if not presentacion:
        raise HTTPException(status_code=404, detail="Presentación no encontrada")

    old_file_url = presentacion.url_foto # Guardar URL antigua por si hay que borrarla
    file_url = old_file_url # Mantener URL existente por defecto

    if file:
        # Guardar nuevo archivo
        file_url = await save_upload_file(upload_file=file, destination_folder="presentaciones") # <--- Usar await
        if not file_url:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo guardar la nueva imagen.")
        # Si la subida fue exitosa y había una foto antigua diferente, borrar la antigua
        if old_file_url and old_file_url != file_url:
             delete_file(old_file_url) # <--- Borrar archivo antiguo


    update_data = {
        "nombre": nombre, "capacidad_kg": capacidad_kg, "tipo": tipo,
        "precio_venta": precio_venta, "activo": activo, "url_foto": file_url
    }
    # Filtrar None values para no sobrescribir con nada si no se envían
    update_data_filtered = {k: v for k, v in update_data.items() if v is not None}

    # Asegurar que la nueva URL (o la antigua si no se subió nada) se incluya si existe
    # y file_url no es None (en caso de error de subida previo, no deberíamos llegar aquí)
    if file_url:
        update_data_filtered['url_foto'] = file_url
    elif 'url_foto' in update_data_filtered and update_data_filtered['url_foto'] is None:
         # Si explícitamente se envió url_foto=None o no se envió archivo nuevo,
         # y queremos borrar la foto existente sin subir una nueva:
         if old_file_url:
             delete_file(old_file_url)
         update_data_filtered['url_foto'] = None # Asegurar que se guarda None

    updated_presentacion = crud.crud_presentacion.update_presentacion(
        db=db, db_obj=presentacion, obj_in=update_data_filtered
    )
    return updated_presentacion


@router.delete("/{presentacion_id}", response_model=schemas.Presentacion)
def delete_presentacion(
    *,
    db: Session = Depends(deps.get_db),
    presentacion_id: int,
    current_user: "Users" = Depends(deps.require_admin), # Ejemplo
) -> Any:
    """Elimina una presentación y su foto asociada si existe."""
    presentacion = crud.crud_presentacion.get_presentacion(db, presentacion_id=presentacion_id)
    if not presentacion:
        raise HTTPException(status_code=404, detail="Presentación no encontrada")

    file_to_delete = presentacion.url_foto # Obtener URL antes de eliminar

    # Eliminar registro de la BD (ON DELETE CASCADE debería manejar dependencias)
    deleted_presentacion = crud.crud_presentacion.delete_presentacion(db=db, presentacion_id=presentacion_id)

    # Si la eliminación de BD fue exitosa, intentar eliminar el archivo
    if deleted_presentacion and file_to_delete:
        delete_file(file_to_delete) # <--- Borrar archivo asociado

    return deleted_presentacion