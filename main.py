# main.py (en la raíz del proyecto)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum # Para AWS Lambda
import uvicorn
from app.api.v1.router import api_router
from app.core.config import settings
# from app.db.session import engine # Opcional: si necesitas interactuar con engine directamente
# from app.db.base import Base # Opcional: si necesitas crear tablas (ej. con init_db)

# Opcional: Crear tablas si no existen (más útil para desarrollo/pruebas)
# NO RECOMENDADO en producción Lambda, usar Alembic
# def init_db_tables():
#     Base.metadata.create_all(bind=engine)
# init_db_tables()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" # URL para el esquema OpenAPI
)

# Configuración CORS
if settings.BACKEND_CORS_ORIGINS:
    # Permite comodín o lista de orígenes
    origins = []
    if isinstance(settings.BACKEND_CORS_ORIGINS, str):
        if settings.BACKEND_CORS_ORIGINS == "*":
            origins.append("*")
        else:
            origins.extend(settings.BACKEND_CORS_ORIGINS.split(","))
    elif isinstance(settings.BACKEND_CORS_ORIGINS, list):
        origins = settings.BACKEND_CORS_ORIGINS

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Incluir el router de la API v1
app.include_router(api_router, prefix=settings.API_V1_STR)

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Handler para AWS Lambda usando Mangum
handler = Mangum(app)

# --- Sección para correr localmente con Uvicorn ---
if __name__ == "__main__":

    # Nota: Uvicorn busca 'app' dentro del archivo 'main.py' por defecto
    # El puerto 5000 es solo un ejemplo para local
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)