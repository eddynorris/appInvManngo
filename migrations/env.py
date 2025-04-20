# migrations/env.py (Corregido para FastAPI)
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# --- Configuración para encontrar tus modelos ---
# Añadir tu directorio 'app' al path para que Alembic lo encuentre
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

# Importar tu Base de SQLAlchemy y settings de Pydantic
from app.db.base import Base  # Asegúrate que esta ruta sea correcta
from app.core.config import settings # Asegúrate que esta ruta sea correcta
# --- Fin Configuración ---

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# --- Configuración de la URL de la Base de Datos ---
# Establecer la URL de la base de datos en la configuración de Alembic
# Lee desde tus settings (que leen desde env vars)
# Asegúrate que DATABASE_URL esté definida en tus settings/env vars
if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL no está configurada en los settings/variables de entorno.")
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)
# --- Fin Configuración DB URL ---

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Usar la URL establecida desde los settings
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # include_schemas=True, # Descomentar si usas schemas de PostgreSQL
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Obtener el engine desde la configuración de Alembic (que usa sqlalchemy.url)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool, # NullPool es recomendado para migraciones
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
            # Puedes añadir otras opciones aquí si las necesitas, por ejemplo:
            # render_as_batch=True # Para SQLite y algunos casos de ALTER
            # include_schemas=True, # Si usas schemas de PostgreSQL
        )

        with context.begin_transaction():
            context.run_migrations()

# Determinar si ejecutar en modo offline u online
if context.is_offline_mode():
    print("Running migrations offline...")
    run_migrations_offline()
else:
    print("Running migrations online...")
    run_migrations_online()

print("Migrations finished.")
