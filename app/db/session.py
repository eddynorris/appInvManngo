from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os

# Lógica para obtener DATABASE_URL (incluyendo Secrets Manager para AWS)
# Esta lógica es simplificada. Para producción en AWS, integrar con Secrets Manager
DATABASE_URL_TO_USE = settings.DATABASE_URL

# Considera pool_pre_ping=True para manejar conexiones inactivas (útil en Lambda)
engine = create_engine(DATABASE_URL_TO_USE, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

print(f"Database engine created for URL ending with: ...{DATABASE_URL_TO_USE[-20:]}") # Log para depuración
