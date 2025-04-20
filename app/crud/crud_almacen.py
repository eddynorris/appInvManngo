# app/crud/crud_almacen.py
from sqlalchemy.orm import Session
from app import models, schemas
# Añadir import para TYPE_CHECKING (opcional pero bueno para linters/mypy)
from typing import TYPE_CHECKING

# Definir el tipo dentro de TYPE_CHECKING para evitar importación real en runtime
# si no es necesaria, pero permite que herramientas de análisis lo vean.
if TYPE_CHECKING:
    from app.models.models import Almacen # Asumiendo que Almacen está en models.py

def get_almacen(db: Session, almacen_id: int):
    # Usar la referencia forward aquí también es buena práctica
    return db.query(models.Almacen).filter(models.Almacen.id == almacen_id).first() # models.Almacen debería funcionar aquí si el modelo está cargado

def get_almacenes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Almacen).offset(skip).limit(limit).all()

def create_almacen(db: Session, almacen: schemas.AlmacenCreate):
    # Asumiendo que Almacen está en app/models/models.py
    # Ajustar si tu modelo Almacen está en otro lugar
    db_almacen = models.Almacen(**almacen.model_dump())
    db.add(db_almacen)
    db.commit()
    db.refresh(db_almacen)
    return db_almacen

# Usar la referencia forward en la anotación de tipo para db_obj
def update_almacen(db: Session, db_obj: "Almacen", obj_in: schemas.AlmacenUpdate | dict): # <--- Cambio aquí
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_almacen(db: Session, almacen_id: int):
    db_obj = db.query(models.Almacen).get(almacen_id)
    if db_obj:
        # Considerar lógica adicional si hay inventario/ventas asociadas
        db.delete(db_obj)
        db.commit()
    return db_obj