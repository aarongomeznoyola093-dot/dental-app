import os
import re

# Lista de archivos a convertir
archivos = [
    "app/controladores/pacientes_controlador.py",
    "app/controladores/pagos_controlador.py", 
    "app/controladores/tratamiento_controlador.py",
    "app/controladores/reportes_controlador.py"
]

for archivo in archivos:
    if os.path.exists(archivo):
        print(f"Procesando {archivo}...")
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Reemplazar imports
        contenido = contenido.replace("from app.db_session import get_db_session", "from app.database import get_db\nfrom sqlalchemy.orm import Session")
        
        # Reemplazar get_db_session() en funciones
        contenido = contenido.replace("session = get_db_session()", "db: Session = Depends(get_db)")
        
        # Reemplazar session.execute con consultas SQLAlchemy (básico)
        # NOTA: Esto es un reemplazo básico, es posible que necesites ajustes manuales
        
        with open(archivo, 'w', encoding='utf-8') as f:
            f.write(contenido)
        print(f"✓ {archivo} procesado")
    else:
        print(f"✗ {archivo} no encontrado")
