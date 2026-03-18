import uuid
import logging
from passlib.context import CryptContext
from cassandra.cluster import Cluster
from app.db_session import connect_to_db, get_session

# --- CONFIGURACIÓN ---
KEYSPACE = "consultorio_dental"
ADMIN_USERNAME = "admin"
ADMIN = "12345"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

# --- CONEXIÓN A CASSANDRA ---
try:
    cluster = Cluster(['127.0.0.1'])
    session = cluster.connect()
    logging.info("Conexión inicial a Cassandra exitosa.")
except Exception as e:
    logging.error(f"No se pudo conectar con Cassandra. Error: {e}")
    exit()

try:
    # Crear Keyspace
    logging.info(f"Asegurando que el keyspace '{KEYSPACE}' exista...")
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
        WITH replication = {{ 'class': 'SimpleStrategy', 'replication_factor': '1' }};
    """)
    session.set_keyspace(KEYSPACE)
    logging.info("Keyspace listo.")

    # -------------------------
    # TABLAS DEL SISTEMA
    # -------------------------

    logging.info("Creando todas las tablas necesarias...")

    session.execute("""
    CREATE TABLE IF NOT EXISTS paciente (
        id_paciente UUID PRIMARY KEY,
        nombre TEXT,
        apellido_pat TEXT,
        apellido_mat TEXT,
        fecha_nacimiento DATE,
        telefono TEXT,
        edad INT,
        enfermedades LIST<TEXT>,
        medicamentos LIST<TEXT>,
        alergias LIST<TEXT>
    );
    """)

    session.execute("""
    CREATE TABLE IF NOT EXISTS cita (
        id_paciente UUID,
        id_cita UUID,
        fecha_hora TIMESTAMP,
        motivo TEXT,
        estado TEXT,
        PRIMARY KEY (id_paciente, id_cita)
    );
    """)

    session.execute("""
    CREATE TABLE IF NOT EXISTS tratamiento (
        id_tratamiento UUID PRIMARY KEY,
        nombre TEXT,
        categoria TEXT,
        descripcion TEXT,
        precio DECIMAL,
        duracion_estimada MAP<TEXT, INT>
    );
    """)

    session.execute("""
    CREATE TABLE IF NOT EXISTS cita_tratamiento (
        id_paciente UUID,
        id_cita UUID,
        id_tratamiento UUID,
        observaciones TEXT,
        resultado TEXT,
        PRIMARY KEY (id_paciente, id_cita, id_tratamiento)
    );
    """)

    session.execute("""
    CREATE TABLE IF NOT EXISTS pago (
        id_paciente UUID,
        id_cita UUID,
        id_pago UUID,
        monto DECIMAL,
        fecha_pago DATE,
        metodo_pago TEXT,
        PRIMARY KEY (id_paciente, id_cita, id_pago)
    );
    """)

    session.execute("""
    CREATE TABLE IF NOT EXISTS abono (
        id_paciente UUID,
        id_abono UUID,
        id_tratamiento UUID,
        fecha_abono DATE,
        monto_abonado DECIMAL,
        saldo_restante DECIMAL,
        estado TEXT,
        PRIMARY KEY (id_paciente, id_abono)
    );
    """)

    # -----------------------------------------
    # TABLA ADMINISTRADOR 100% CORREGIDA
    # -----------------------------------------
    session.execute("""
    CREATE TABLE IF NOT EXISTS administrador (
        id_admin UUID PRIMARY KEY,
        username TEXT,
        hashed_password TEXT,
        intentos_fallidos INT,
        bloqueado_hasta TIMESTAMP
    );
    """)

    # Índice
    session.execute("CREATE INDEX IF NOT EXISTS admin_username_idx ON administrador (username);")

    # -------------------------
    # REGISTRO ADMIN POR DEFECTO
    # -------------------------
    rows = session.execute(
        "SELECT username FROM administrador WHERE username = %s ALLOW FILTERING",
        [ADMIN_USERNAME]
    )

    if rows.one():
        logging.info(f"El usuario administrador '{ADMIN_USERNAME}' ya existe.")
    else:
        hashed_password = get_password_hash(ADMIN)
        session.execute(
            "INSERT INTO administrador (id_admin, username, hashed_password, intentos_fallidos, bloqueado_hasta) VALUES (%s, %s, %s, %s, %s)",
            (uuid.uuid4(), ADMIN_USERNAME, hashed_password, 0, None)
        )
        logging.info(f"Administrador '{ADMIN_USERNAME}' creado correctamente.")
        logging.info(f"Contraseña: {ADMIN}")

    # -------------------------
    # TABLA REGISTROS PENDIENTES
    # -------------------------
    session.execute("""
    CREATE TABLE IF NOT EXISTS pending_registration (
        email text PRIMARY KEY,
        verification_code text,
        expires_at timestamp
    );
    """)

    logging.info("Todas las tablas fueron creadas correctamente.")

except Exception as e:
    logging.error(f"Error durante la configuración: {e}")

finally:
    cluster.shutdown()
    logging.info("Conexión cerrada correctamente.")
