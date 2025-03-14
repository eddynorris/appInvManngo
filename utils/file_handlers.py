import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    """Verifica si la extensión del archivo es permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_file(file, subfolder):
    """
    Guarda un archivo en el sistema de archivos.
    
    Args:
        file: Objeto de archivo de Flask request.files
        subfolder: Carpeta dentro de UPLOAD_FOLDER donde guardar
        
    Returns:
        str: Ruta relativa al archivo guardado o None si hay error
    """
    if file and allowed_file(file.filename):
        # Generar nombre seguro único
        original_filename = secure_filename(file.filename)
        extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{extension}"
        
        # Crear ruta completa
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
        file_path = os.path.join(save_path, unique_filename)
        
        # Guardar archivo
        try:
            os.makedirs(save_path, exist_ok=True)
            file.save(file_path)
            # Retornar ruta relativa para almacenar en BD
            return os.path.join(subfolder, unique_filename)
        except Exception as e:
            current_app.logger.error(f"Error guardando archivo: {str(e)}")
            return None
    
    return None

def delete_file(file_path):
    """Elimina un archivo si existe"""
    if not file_path:
        return False
        
    # Construir ruta completa
    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
    
    # Verificar que existe y eliminar
    try:
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
    except Exception as e:
        current_app.logger.error(f"Error eliminando archivo: {str(e)}")
    
    return False