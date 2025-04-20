# update_password.py
from app.db.session import SessionLocal
from app.crud import crud_user
from app.core import security
db = SessionLocal()
username_to_update = "eddy"
new_password_plain = "123456" # La contraseña que quieres establecer
user = crud_user.get_user_by_username(db, username=username_to_update)
if user:
    print(f"Usuario '{username_to_update}' encontrado. Actualizando contraseña...")
    hashed_password = security.get_password_hash(new_password_plain)
    user.password = hashed_password
    db.add(user) # Añadir al contexto de sesión para marcarlo como modificado
    db.commit()
    print(f"Contraseña actualizada exitosamente para '{username_to_update}'.")
else:
    print(f"Usuario '{username_to_update}' no encontrado.")
db.close()