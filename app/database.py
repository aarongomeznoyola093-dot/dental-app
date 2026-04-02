import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Detectar si estamos en producción o desarrollo
IS_PRODUCTION = os.getenv("RENDER") == "true" or os.getenv("DATABASE_URL") is not None

if IS_PRODUCTION:
    # PRODUCCIÓN (Render / PostgreSQL)
    DATABASE_URL = os.getenv("DATABASE_URL")
    print("🔧 Modo PRODUCCIÓN - Conectando a la base de datos")

    engine = create_engine(DATABASE_URL)

else:
    # DESARROLLO LOCAL (SQLite)
    DATABASE_URL = "sqlite:///./consultorio_dental.db"
    print("🔧 Modo DESARROLLO - Usando SQLite local")

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

# Crear sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()


# Dependencia para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()