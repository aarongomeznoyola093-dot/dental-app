import os
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import dict_factory
from dotenv import load_dotenv

load_dotenv()

# Configuración de Astra (usando el token y bundle que ya funcionaron)
ASTRA_TOKEN = os.getenv("ASTRA_TOKEN")
ASTRA_SECURE_BUNDLE_PATH = os.getenv("ASTRA_SECURE_BUNDLE_PATH")
KEYSPACE = os.getenv("KEYSPACE", "consultorio_dental")

session = None

def get_db_session():
    global session
    if session is None:
        try:
            print("--- CONECTANDO A ASTRA ---")
            print(f"🔍 ASTRA_TOKEN: {'*' * 10 if ASTRA_TOKEN else 'NO CONFIGURADO'}")
            print(f"🔍 ASTRA_SECURE_BUNDLE_PATH: {ASTRA_SECURE_BUNDLE_PATH}")
            print(f"🔍 KEYSPACE: {KEYSPACE}")
            
            # Validar que las variables estén configuradas
            if not ASTRA_TOKEN:
                print("❌ Error: ASTRA_TOKEN no está configurado en las variables de entorno")
                return None
            if not ASTRA_SECURE_BUNDLE_PATH:
                print("❌ Error: ASTRA_SECURE_BUNDLE_PATH no está configurado en las variables de entorno")
                return None
            
            cloud_config = {
                'secure_connect_bundle': ASTRA_SECURE_BUNDLE_PATH
            }
            auth_provider = PlainTextAuthProvider('token', ASTRA_TOKEN)
            
            cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
            session = cluster.connect(KEYSPACE)
            session.row_factory = dict_factory
            
            print("--- CONEXIÓN EXITOSA A ASTRA ---")
            
        except Exception as e:
            print(f"❌ Error conectando a Astra: {e}")
            import traceback
            traceback.print_exc()
            session = None
    
    return session