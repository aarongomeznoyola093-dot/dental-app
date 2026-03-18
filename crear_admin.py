import uuid
from cassandra.cluster import Cluster
from passlib.context import CryptContext

ADMIN_USERNAME = "admin"
ADMIN = "12345"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    """Toma una contraseña en texto plano y devuelve su versión encriptada (hash)."""
    return pwd_context.hash(password)

# --- CONEXIÓN A CASSANDRA ---
try:
    cluster = Cluster(['127.0.0.1'])
    session = cluster.connect('consultorio_dental')
    print(" Conexión a Cassandra exitosa.")
except Exception as e:
    print(f" Error al conectar con Cassandra: {e}")
    exit()

try:
    print("1. Creando la tabla 'administrador' si no existe...")
    session.execute("""
    CREATE TABLE IF NOT EXISTS administrador (
        id_admin UUID PRIMARY KEY,
        username TEXT,
        hashed_password TEXT
    );
    """)
    print("   ... Tabla 'administrador' asegurada.")

    print("2. Creando índice estándar en 'username'...")
    session.execute("""
    CREATE INDEX IF NOT EXISTS admin_username_std_idx ON administrador (username);
    """)
    print("   ... Índice estándar asegurado.")

    print(f"3. Verificando si el usuario '{ADMIN_USERNAME}' ya existe...")
    rows = session.execute("SELECT * FROM administrador WHERE username = %s", [ADMIN_USERNAME])
    if rows.one():
        print(f"   ... ¡El usuario '{ADMIN_USERNAME}' ya existe! No se necesita hacer nada.")
    else:
        print(f"   ... Creando el usuario '{ADMIN_USERNAME}'...")
        hashed_password = get_password_hash(ADMIN)
        session.execute(
            "INSERT INTO administrador (id_admin, username, hashed_password) VALUES (%s, %s, %s)",
            (uuid.uuid4(), ADMIN_USERNAME, hashed_password)
        )
        print(" ¡Usuario administrador creado exitosamente!")
        print(f"   - Usuario: {ADMIN_USERNAME}")
        print(f"   - Contraseña: {ADMIN}")

except Exception as e:
    print(f" Ocurrió un error durante la creación: {e}")
finally:
    cluster.shutdown()
    print(" Conexión a Cassandra cerrada.")

