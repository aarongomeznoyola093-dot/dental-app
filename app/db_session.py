import os
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import dict_factory
from dotenv import load_dotenv

load_dotenv()

# Configuración de Astra (usando el token y bundle que ya funcionaron)
ASTRA_TOKEN = os.getenv("ASTRA_TOKEN", "AstraCS:RarYRzyPCdNNBMaBbSwJjozc:b973381ce1c2ab649ee7d5a6bb1e20dbe74a28cadd537391327422487803d685")
ASTRA_SECURE_BUNDLE_PATH = os.getenv("ASTRA_SECURE_BUNDLE_PATH", "secure-connect-dental-db.zip")
KEYSPACE = os.getenv("KEYSPACE", "consultorio_dental")

session = None

def get_db_session():
    global session
    if session is None:
        try:
            print("--- CONECTANDO A ASTRA ---")
            
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
            session = None
    
    return session