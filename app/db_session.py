import os
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import dict_factory
from cassandra.policies import DCAwareRoundRobinPolicy

session = None

def get_db_session():
    global session
    if session is None:
        try:
            print("--- CONECTANDO A ASTRA (DRIVER CQL) ---")
            
            ASTRA_TOKEN = os.getenv("ASTRA_TOKEN")
            ASTRA_HOST = os.getenv("ASTRA_HOST")  # ← Nueva variable
            KEYSPACE = os.getenv("KEYSPACE", "consultorio_dental")
            
            print(f"🔍 ASTRA_HOST: {ASTRA_HOST}")
            print(f"🔍 KEYSPACE: {KEYSPACE}")
            
            if not ASTRA_TOKEN:
                print("❌ ERROR: ASTRA_TOKEN no está configurado")
                return None
            if not ASTRA_HOST:
                print("❌ ERROR: ASTRA_HOST no está configurado")
                return None
            
            auth_provider = PlainTextAuthProvider('token', ASTRA_TOKEN)
            
            # Política de balanceo para la región
            # Extraer región del host (us-east-2)
            region = "us-east-2"
            lbp = DCAwareRoundRobinPolicy(local_dc=region)
            
            cluster = Cluster(
                [ASTRA_HOST],
                port=9042,
                auth_provider=auth_provider,
                load_balancing_policy=lbp,
                ssl_options={'ca_certs': None},
                protocol_version=4
            )
            session = cluster.connect(KEYSPACE)
            session.row_factory = dict_factory
            
            print("--- CONEXIÓN EXITOSA A ASTRA (DRIVER CQL) ---")
            
        except Exception as e:
            print(f"❌ Error conectando a Astra: {e}")
            import traceback
            traceback.print_exc()
            session = None
    
    return session