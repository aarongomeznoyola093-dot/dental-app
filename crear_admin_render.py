import psycopg2
import uuid

# ========== TUS DATOS DE RENDER ==========
HOST = "dpg-d73islpr0fns73chnjo0-a.oregon-postgres.render.com"
PORT = 5432
DATABASE = "consultorio_dental_wxgb"
USER = "dental_user"
PASSWORD = "TZcGq9YeWCgo58NoY6rOhdpPVFyECW7f"
# ========================================

try:
    print("Conectando a PostgreSQL en Render...")
    print(f"Host: {HOST}")
    
    conn = psycopg2.connect(
        host=HOST,
        port=PORT,
        database=DATABASE,
        user=USER,
        password=PASSWORD,
        sslmode='require'
    )
    print("✅ Conexión exitosa")
    
    cur = conn.cursor()
    
    # Verificar si la tabla existe
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'administradores'
        )
    """)
    existe = cur.fetchone()[0]
    
    if existe:
        print("⚠️ La tabla 'administradores' ya existe, eliminando...")
        cur.execute("DROP TABLE administradores CASCADE")
        conn.commit()
        print("✅ Tabla eliminada")
    
    # Crear tabla con UUID
    cur.execute("""
        CREATE TABLE administradores (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            intentos_fallidos INTEGER DEFAULT 0,
            bloqueado_hasta TIMESTAMP,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            activo BOOLEAN DEFAULT TRUE
        )
    """)
    conn.commit()
    print("✅ Tabla 'administradores' creada correctamente")
    
    # Hash de la contraseña "12345" (bcrypt)
    hashed = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    
    # Insertar administrador
    cur.execute("""
        INSERT INTO administradores (username, email, hashed_password, intentos_fallidos)
        VALUES ('admin', 'admin@example.com', %s, 0)
    """, (hashed,))
    conn.commit()
    print("✅ Administrador insertado")
    
    # Verificar
    cur.execute("SELECT id, username FROM administradores WHERE username = 'admin'")
    admin = cur.fetchone()
    if admin:
        print(f"\n🎉 ¡ÉXITO! Administrador creado correctamente")
        print(f"   ID: {admin[0]}")
        print(f"   Usuario: {admin[1]}")
        print(f"   Contraseña: 12345")
    else:
        print("⚠️ Error: No se pudo crear el administrador")
    
    # Mostrar todos los administradores
    cur.execute("SELECT id, username, email FROM administradores")
    print("\n📋 Administradores en la base de datos:")
    for row in cur.fetchall():
        print(f"   - ID: {row[0]}, Usuario: {row[1]}, Email: {row[2]}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    if 'conn' in locals():
        conn.rollback()