import os
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import dict_factory

# Configuración de Astra - SOLO variables de entorno
ASTRA_TOKEN = os.getenv("ASTRA_TOKEN")
ASTRA_ENDPOINT = os.getenv("ASTRA_ENDPOINT")
KEYSPACE = os.getenv("KEYSPACE", "consultorio_dental")

session = None

def get_db_session():
    global session
    if session is None:
        try:
            print("--- CONECTANDO A ASTRA (SIN BUNDLE) ---")
            print(f"🔍 ASTRA_TOKEN: {'[CONFIGURADO]' if ASTRA_TOKEN else '[NO CONFIGURADO]'}")
            print(f"🔍 ASTRA_ENDPOINT: {ASTRA_ENDPOINT}")
            print(f"🔍 KEYSPACE: {KEYSPACE}")
            
            if not ASTRA_TOKEN:
                print("❌ ERROR: ASTRA_TOKEN no está configurado")
                return None
            if not ASTRA_ENDPOINT:
                print("❌ ERROR: ASTRA_ENDPOINT no está configurado")
                return None
            
            # Extraer el host correctamente (eliminar https:// y la parte después de la barra)
            host = ASTRA_ENDPOINT.replace("https://", "").split("/")[0]
            print(f"🔍 Host extraído: {host}")
            
            port = 9042
            
            auth_provider = PlainTextAuthProvider('token', ASTRA_TOKEN)
            
            cluster = Cluster([host], port=port, auth_provider=auth_provider, ssl_options=True)
            session = cluster.connect(KEYSPACE)
            session.row_factory = dict_factory
            
            print("--- CONEXIÓN EXITOSA A ASTRA (SIN BUNDLE) ---")
            
        except Exception as e:
            print(f"❌ Error conectando a Astra: {e}")
            import traceback
            traceback.print_exc()
            session = None
    
    return session