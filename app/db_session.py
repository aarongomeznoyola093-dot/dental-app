import os
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import dict_factory

# NO USAR dotenv en producción, Render ya tiene las variables
# load_dotenv()  # COMENTADO o ELIMINADO

# Configuración de Astra - SOLO variables de entorno, SIN valores por defecto
ASTRA_TOKEN = os.getenv("ASTRA_TOKEN")
ASTRA_ENDPOINT = os.getenv("ASTRA_ENDPOINT")  # ← NUEVA variable
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
            
            # Extraer host del endpoint (sin https:// y sin /)
            host = ASTRA_ENDPOINT.replace("https://", "bd8ae16a-c748-418b-b285-0529d4b18fa8-us-east-2.apps.astra.datastax.com").split("/")[0]
            port = 9042  # Puerto por defecto de Cassandra
            
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