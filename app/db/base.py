from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

# Configuración de metadatos para Alembic si usas convenciones de nombrado
# convention = {
#     "ix": "ix_%(column_0_label)s",
#     "uq": "uq_%(table_name)s_%(column_0_name)s",
#     "ck": "ck_%(table_name)s_%(constraint_name)s",
#     "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
#     "pk": "pk_%(table_name)s"
# }
# metadata = MetaData(naming_convention=convention)

class Base(DeclarativeBase):
    # metadata = metadata # Descomentar si usas la convención de nombrado arriba
    pass

# IMPORTANTE: Asegúrate de que tus modelos en app/models/__init__.py
# hereden de esta clase Base
