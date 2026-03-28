import psycopg2

HOST = "dpg-d73islpr0fns73chnjo0-a.oregon-postgres.render.com"
PORT = 5432
DATABASE = "consultorio_dental_wxgb"
USER = "dental_user"
PASSWORD = "TZcGq9YeWCgo58NoY6rOhdpPVFyECW7f"

# Hash correcto de la contraseña "12345"
hash_correcto = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"

conn = psycopg2.connect(
    host=HOST,
    port=PORT,
    database=DATABASE,
    user=USER,
    password=PASSWORD,
    sslmode='require'
)
cur = conn.cursor()

# Actualizar la contraseña
cur.execute("""
    UPDATE administradores 
    SET hashed_password = %s, intentos_fallidos = 0, bloqueado_hasta = NULL
    WHERE username = 'admin'
""", (hash_correcto,))
conn.commit()

print("✅ Contraseña actualizada correctamente")
print("   Usuario: admin")
print("   Contraseña: 12345")

# Verificar
cur.execute("SELECT username, hashed_password FROM administradores WHERE username = 'admin'")
admin = cur.fetchone()
print(f"Hash almacenado: {admin[1][:50]}...")

cur.close()
conn.close()