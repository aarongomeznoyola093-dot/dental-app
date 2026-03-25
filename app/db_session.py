import os
from astrapy import DataAPIClient

# Variables de entorno (las que ya tienes en Render)
ASTRA_TOKEN = os.getenv("ASTRA_TOKEN")
ASTRA_API_ENDPOINT = os.getenv("ASTRA_API_ENDPOINT")
KEYSPACE = os.getenv("KEYSPACE", "default_keyspace")

db = None

def get_db_session():
    global db

    if db is None:
        try:
            print("\n--- CONECTANDO A ASTRA (Data API) ---")

            if not ASTRA_TOKEN:
                print("❌ ERROR: ASTRA_TOKEN no configurado")
                return None

            if not ASTRA_API_ENDPOINT:
                print("❌ ERROR: ASTRA_API_ENDPOINT no configurado")
                return None

            print("🔑 Token detectado")
            print("🌐 Endpoint detectado")
            print(f"📦 Keyspace: {KEYSPACE}")

            client = DataAPIClient(ASTRA_TOKEN)

            db = client.get_database_by_api_endpoint(
                ASTRA_API_ENDPOINT,
                keyspace=KEYSPACE
            )

            print("✅ Conexión exitosa a Astra DB")

        except Exception as e:
            print(f"❌ Error conectando a Astra: {e}")
            db = None

    return db