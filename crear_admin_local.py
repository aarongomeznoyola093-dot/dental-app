import sqlite3
import bcrypt

print("Conectando a SQLite...")

# Conectar a la base de datos
conn = sqlite3.connect('consultorio_dental.db')
cursor = conn.cursor()

# Crear tabla administradores
cursor.execute('''
    CREATE TABLE IF NOT EXISTS administradores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        intentos_fallidos INTEGER DEFAULT 0,
        bloqueado_hasta TEXT,
        creado_en TEXT DEFAULT CURRENT_TIMESTAMP,
        activo INTEGER DEFAULT 1
    )
''')
conn.commit()
print("✅ Tabla 'administradores' creada")

# Hash de la contraseña "12345" usando bcrypt directamente
password = "12345"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(f"Hash generado: {hashed[:50]}...")

# Verificar si ya existe
cursor.execute("SELECT username FROM administradores WHERE username = 'admin'")
existe = cursor.fetchone()

if existe:
    print("⚠️ Administrador ya existe, actualizando contraseña...")
    cursor.execute("UPDATE administradores SET hashed_password = ?, intentos_fallidos = 0 WHERE username = 'admin'", (hashed,))
else:
    print("✅ Creando administrador...")
    cursor.execute('''
        INSERT INTO administradores (username, email, hashed_password, intentos_fallidos)
        VALUES (?, ?, ?, 0)
    ''', ('admin', 'admin@example.com', hashed))

conn.commit()
print("✅ Administrador guardado")

# Verificar
cursor.execute("SELECT id, username, hashed_password FROM administradores WHERE username = 'admin'")
admin = cursor.fetchone()
if admin:
    print(f"\n🎉 ¡ÉXITO!")
    print(f"   ID: {admin[0]}")
    print(f"   Usuario: {admin[1]}")
    print(f"   Hash: {admin[2][:50]}...")
    print(f"\n   Contraseña: {password}")
    
    # Verificar que la contraseña funciona
    if bcrypt.checkpw(password.encode('utf-8'), admin[2].encode('utf-8')):
        print("   ✅ Verificación: Contraseña correcta")
    else:
        print("   ❌ Verificación: Contraseña incorrecta")
else:
    print("❌ Error: No se pudo crear el administrador")

# Mostrar todos los administradores
cursor.execute("SELECT id, username, email FROM administradores")
print("\n📋 Administradores:")
for row in cursor.fetchall():
    print(f"   - ID: {row[0]}, Usuario: {row[1]}, Email: {row[2]}")

conn.close()
print("\n✅ Base de datos lista")