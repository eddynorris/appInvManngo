# Usa una versión estable de Python
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema (si alguna librería las necesita)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copiar archivo de dependencias
COPY requirements.txt .

# Instalar dependencias
# Usar --no-cache-dir para reducir tamaño de imagen
# Considera usar multi-stage builds para optimizar más
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código de la aplicación (después de instalar dependencias para caché)
COPY ./app /app/app
COPY main.py .
COPY migrations/ /app/migrations/ # Incluir migraciones
COPY alembic.ini . # Incluir config de Alembic

# Nota: El CMD no es estrictamente necesario para Lambda con Mangum,
# pero es útil para probar el contenedor localmente.
# Uvicorn correrá en el puerto 80 por defecto dentro del contenedor.
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]