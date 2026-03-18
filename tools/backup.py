import sys
import os
import json
from datetime import datetime, date


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db_session import get_session, connect_to_db

def serializar_dato(dato):
    """
    Convierte recursivamente cualquier dato extraño de Cassandra 
    (Fechas, UUIDs, Mapas, Sets) a tipos nativos de Python compatibles con JSON.
    """
   
    if dato is None:
        return None


    if isinstance(dato, (datetime, date)):
        return dato.isoformat()
    
 
    if type(dato).__name__ == 'Date':
        return str(dato)

    
    if hasattr(dato, 'hex'): 
        return str(dato)

    
    if hasattr(dato, 'as_tuple'): 
        return float(dato)

    
    if isinstance(dato, dict) or 'Map' in type(dato).__name__:
        
        return {str(k): serializar_dato(v) for k, v in dato.items()}

    
    if hasattr(dato, '__iter__') and not isinstance(dato, (str, bytes)):
        return [serializar_dato(x) for x in dato]

    
    return dato

def realizar_backup():
    print("--- INICIANDO RESPALDO ---")
    
    try:
        connect_to_db()
        session = get_session()
    except Exception as e:
        print(f"Error crítico conectando a BD: {e}")
        return

    if not session:
        print("Error: No hay sesión de base de datos.")
        return

    
    fecha_hoy = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    carpeta_backup = f"backups/{fecha_hoy}"
    os.makedirs(carpeta_backup, exist_ok=True)

    
    tablas = ["paciente", "tratamiento", "cita", "pago", "abono", "cita_tratamiento", "administrador"]

    for tabla in tablas:
        print(f"Respaldando tabla: {tabla}...")
        try:
            rows = session.execute(f"SELECT * FROM {tabla}")
            datos = []
            
            for row in rows:
                fila_dict = {}
                
                
                if isinstance(row, dict):
                    for key, val in row.items():
                        fila_dict[key] = serializar_dato(val)
                else:
                    
                    columnas = []
                    if hasattr(row, '_fields'):
                        columnas = row._fields
                    elif hasattr(row, '__dict__'):
                        columnas = row.__dict__.keys()
                    
                    for key in columnas:
                        
                        if key.startswith('_'): continue
                        val = getattr(row, key)
                        fila_dict[key] = serializar_dato(val)
                
                datos.append(fila_dict)
            
            
            ruta_archivo = f"{carpeta_backup}/{tabla}.json"
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            
            print(f"  -> Guardado: {len(datos)} registros en {ruta_archivo}")

        except Exception as e:
            print(f"  -> ERROR en tabla {tabla}: {e}")

    print("--- RESPALDO COMPLETADO ---")
    print(f"Archivos guardados en: {carpeta_backup}")

if __name__ == "__main__":
    realizar_backup()