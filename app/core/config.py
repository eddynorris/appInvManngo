# app/core/config.py
import os
from pydantic_settings import BaseSettings
from typing import List, Union
from dotenv import load_dotenv

# Cargar .env solo para desarrollo local o si existe
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Manngo API"
    API_V1_STR: str = "/api/v1"

    # Base de datos (Lee desde .env o variables de entorno del sistema)
    # Asegúrate de tener estas variables en tu entorno Lambda/local
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:123456@localhost/manngo_db")

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "albinalabanalabinbonban") # ¡CAMBIAR EN PRODUCCIÓN!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 1 # 1 día

    # CORS
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = os.getenv("ALLOWED_ORIGINS", "*")

    # Configuración de archivos (para S3 en producción/Lambda)
    STORAGE_MODE: str = os.getenv("STORAGE_MODE", "local") # 'local' o 's3'
    S3_BUCKET_NAME: str | None = os.getenv("S3_BUCKET_NAME")
    AWS_ACCESS_KEY_ID: str | None = os.getenv("AWS_ACCESS_KEY_ID") # Mejor usar roles IAM en AWS
    AWS_SECRET_ACCESS_KEY: str | None = os.getenv("AWS_SECRET_ACCESS_KEY") # Mejor usar roles IAM
    AWS_REGION: str | None = os.getenv("AWS_REGION", "us-east-1")

    class Config:
        case_sensitive = True
        # Si usas un archivo .env local para desarrollo:
        # env_file = ".env"
        # env_file_encoding = 'utf-8'

settings = Settings()

# Nota: Para AWS Lambda, las variables de entorno (DATABASE_URL, SECRET_KEY, etc.)
# se configurarán a través de la plantilla SAM o la consola Lambda,
# leyendo idealmente desde AWS Secrets Manager para datos sensibles.
# El código para leer de Secrets Manager iría en app/db/session.py
# o se pasaría directamente a la configuración de la función Lambda.