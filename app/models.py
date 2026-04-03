from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, Date, JSON
from app.database import Base
import uuid
from datetime import datetime

# ==========================================================
# ADMINISTRADOR
# ==========================================================
class Administrador(Base):
    __tablename__ = "administradores"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    intentos_fallidos = Column(Integer, default=0)
    bloqueado_hasta = Column(DateTime, nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)


# ==========================================================
# PACIENTE
# ==========================================================
class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = Column(String(100), nullable=False)
    apellido_pat = Column(String(100), nullable=False)
    apellido_mat = Column(String(100))
    fecha_nacimiento = Column(Date)
    telefono = Column(String(20))
    edad = Column(Integer)

    # 🔥 CAMBIO IMPORTANTE (SQLite compatible)
    enfermedades = Column(Text, default='[]')
    medicamentos = Column(Text, default='[]')
    alergias = Column(Text, default='[]')

    creado_en = Column(DateTime, default=datetime.utcnow)


# ==========================================================
# CITA
# ==========================================================
class Cita(Base):
    __tablename__ = "citas"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    id_paciente = Column(String, nullable=False, index=True)
    fecha_hora = Column(DateTime, nullable=False)
    motivo = Column(String(255))
    estado = Column(String(50), default="programada")
    creado_en = Column(DateTime, default=datetime.utcnow)


# ==========================================================
# TRATAMIENTO
# ==========================================================
class Tratamiento(Base):
    __tablename__ = "tratamientos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = Column(String(100), nullable=False)
    categoria = Column(String(100))
    descripcion = Column(Text)
    precio = Column(Float, default=0)
    duracion_estimada = Column(String(50))
    creado_en = Column(DateTime, default=datetime.utcnow)


# ==========================================================
# CITA - TRATAMIENTO
# ==========================================================
class CitaTratamiento(Base):
    __tablename__ = "citas_tratamientos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_cita = Column(String, nullable=False, index=True)
    id_tratamiento = Column(String, nullable=False)
    observaciones = Column(Text)
    resultado = Column(Text)
    creado_en = Column(DateTime, default=datetime.utcnow)


# ==========================================================
# PAGOS
# ==========================================================
class Pago(Base):
    __tablename__ = "pagos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    id_cita = Column(String, nullable=False, index=True)
    id_paciente = Column(String, nullable=False)
    monto = Column(Float, nullable=False)
    fecha_pago = Column(Date, nullable=False)
    metodo_pago = Column(String(50))
    creado_en = Column(DateTime, default=datetime.utcnow)


# ==========================================================
# ABONOS
# ==========================================================
class Abono(Base):
    __tablename__ = "abonos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    id_paciente = Column(String, nullable=False, index=True)
    id_tratamiento = Column(String, nullable=True)
    fecha_abono = Column(Date, nullable=False)
    monto_abonado = Column(Float, nullable=False)
    saldo_restante = Column(Float, nullable=False)
    estado = Column(String(50), default="Pendiente")
    creado_en = Column(DateTime, default=datetime.utcnow)


# ==========================================================
# REGISTROS PENDIENTES
# ==========================================================
class PendingRegistration(Base):
    __tablename__ = "registros_pendientes"

    email = Column(String(255), primary_key=True)
    verification_code = Column(String(10), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow)