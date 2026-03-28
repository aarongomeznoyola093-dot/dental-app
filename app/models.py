from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, Date
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.database import Base
import uuid
from datetime import datetime

class Administrador(Base):
    __tablename__ = "administradores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    intentos_fallidos = Column(Integer, default=0)
    bloqueado_hasta = Column(DateTime, nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)

class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False)
    apellido_pat = Column(String(100), nullable=False)
    apellido_mat = Column(String(100))
    fecha_nacimiento = Column(Date)
    telefono = Column(String(20))
    edad = Column(Integer)
    enfermedades = Column(ARRAY(String), default=[])
    medicamentos = Column(ARRAY(String), default=[])
    alergias = Column(ARRAY(String), default=[])
    creado_en = Column(DateTime, default=datetime.utcnow)

class Cita(Base):
    __tablename__ = "citas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_paciente = Column(UUID(as_uuid=True), nullable=False, index=True)
    fecha_hora = Column(DateTime, nullable=False)
    motivo = Column(String(255))
    estado = Column(String(50), default="programada")
    creado_en = Column(DateTime, default=datetime.utcnow)

class Tratamiento(Base):
    __tablename__ = "tratamientos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False)
    categoria = Column(String(100))
    descripcion = Column(Text)
    precio = Column(Float, default=0)
    duracion_estimada = Column(String(50))
    creado_en = Column(DateTime, default=datetime.utcnow)

class CitaTratamiento(Base):
    __tablename__ = "citas_tratamientos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_cita = Column(UUID(as_uuid=True), nullable=False, index=True)
    id_tratamiento = Column(UUID(as_uuid=True), nullable=False)
    observaciones = Column(Text)
    resultado = Column(Text)
    creado_en = Column(DateTime, default=datetime.utcnow)

class Pago(Base):
    __tablename__ = "pagos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_cita = Column(UUID(as_uuid=True), nullable=False, index=True)
    id_paciente = Column(UUID(as_uuid=True), nullable=False)
    monto = Column(Float, nullable=False)
    fecha_pago = Column(Date, nullable=False)
    metodo_pago = Column(String(50))
    creado_en = Column(DateTime, default=datetime.utcnow)

class Abono(Base):
    __tablename__ = "abonos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_paciente = Column(UUID(as_uuid=True), nullable=False, index=True)
    id_tratamiento = Column(UUID(as_uuid=True), nullable=True)
    fecha_abono = Column(Date, nullable=False)
    monto_abonado = Column(Float, nullable=False)
    saldo_restante = Column(Float, nullable=False)
    estado = Column(String(50), default="Pendiente")
    creado_en = Column(DateTime, default=datetime.utcnow)

class PendingRegistration(Base):
    __tablename__ = "registros_pendientes"

    email = Column(String(255), primary_key=True)
    verification_code = Column(String(10), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow)