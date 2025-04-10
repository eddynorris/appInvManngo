# utils/file_handlers.py
import os
import uuid
import logging
from werkzeug.utils import secure_filename
from flask import current_app

# Configurar logging
logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Verifica si la extensión del archivo es permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_EXTENSIONS', {})

def safe_filename(filename):
    """Genera un nombre de archivo seguro y único"""
    if not filename:
        return None
        
    # Limpiar el nombre original
    safe_name = secure_filename(filename)
    
    # Si secure_filename retorna un string vacío (ej. solo caracteres inválidos)
    if not safe_name:
        safe_name = 'file'
    
    # Extraer extensión o usar 'bin' como fallback
    try:
        extension = safe_name.rsplit('.', 1)[1].lower()
    except IndexError:
        extension = 'bin'
    
    # Generar nombre único con UUID
    unique_name = f"{uuid.uuid4().hex}.{extension}"
    
    return unique_name

def save_file(file, subfolder):
    """
    Guarda un archivo en el sistema de archivos de forma segura.
    
    Args:
        file: Objeto de archivo de Flask request.files
        subfolder: Carpeta dentro de UPLOAD_FOLDER donde guardar
        
    Returns:
        str: Ruta relativa al archivo guardado o None si hay error
    """
    if not file:
        logger.warning("Intento de guardar archivo vacío")
        return None
        
    # Verificar que el archivo es permitido
    if not allowed_file(file.filename):
        logger.warning(f"Intento de subir archivo con tipo no permitido: {file.filename}")
        return None
    
    # Generar nombre seguro único
    unique_filename = safe_filename(file.filename)
    
    # Verificar que el subfolder no contiene caracteres peligrosos
    if '..' in subfolder or subfolder.startswith('/'):
        logger.error(f"Intento de usar subfolder potencialmente peligroso: {subfolder}")
        return None
    
    # Crear ruta completa (validando path)
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    save_path = os.path.normpath(os.path.join(upload_folder, subfolder))
    
    # Verificar que no estamos saliendo del directorio base
    if not save_path.startswith(os.path.normpath(upload_folder)):
        logger.error(f"Intento de path traversal detectado: {subfolder}")
        return None
    
    file_path = os.path.join(save_path, unique_filename)
    
    # Guardar archivo
    try:
        os.makedirs(save_path, exist_ok=True)
        file.save(file_path)
        logger.info(f"Archivo guardado exitosamente: {file_path}")
        # Retornar ruta relativa para almacenar en BD
        return os.path.join(subfolder, unique_filename)
    except Exception as e:
        logger.error(f"Error guardando archivo: {str(e)}")
        return None

def delete_file(file_path):
    """Elimina un archivo si existe de forma segura"""
    if not file_path:
        return False
    
    # Prevenir path traversal
    if '..' in file_path or file_path.startswith('/'):
        logger.error(f"Intento de borrado de archivo con path peligroso: {file_path}")
        return False
    
    # Construir ruta completa
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    full_path = os.path.normpath(os.path.join(upload_folder, file_path))
    
    # Verificar que no salimos del directorio base
    if not full_path.startswith(os.path.normpath(upload_folder)):
        logger.error(f"Intento de path traversal en delete_file: {file_path}")
        return False
    
    # Verificar que existe y eliminar
    try:
        if os.path.exists(full_path) and os.path.isfile(full_path):
            os.remove(full_path)
            logger.info(f"Archivo eliminado exitosamente: {full_path}")
            return True
        else:
            logger.warning(f"Archivo no encontrado para eliminar: {full_path}")
            return False
    except Exception as e:
        logger.error(f"Error eliminando archivo: {str(e)}")
        return False

def get_file_url(file_path):
    """
    Obtiene la URL completa para acceder a un archivo
    Útil cuando se cambia entre almacenamiento local y cloud
    """
    if not file_path:
        return None
    
    # En caso de almacenamiento local
    storage_mode = os.environ.get('STORAGE_MODE', 'local')
    
    if storage_mode == 'local':
        base_url = os.environ.get('API_BASE_URL', '')
        return f"{base_url}/uploads/{file_path}"
    else:
        # Aquí se puede implementar la lógica para otros sistemas de almacenamiento
        # como Google Cloud Storage, S3, etc.
        return file_path