from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Administrador, PendingRegistration
from app.servicios import auth_servicio
from app.servicios.email_servicio import send_verification_code
from app.limiter import limiter
import uuid
import random
import re
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/admin", tags=["Admin"])

# Modelos Pydantic
class RegistrationRequest(BaseModel):
    email: EmailStr

class RegistrationCompletion(BaseModel):
    email: EmailStr
    password: str
    verification_code: str


@router.post("/token")
@limiter.limit("5/minute")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login de administrador"""
    try:
        # Buscar administrador por username
        admin = db.query(Administrador).filter(
            Administrador.username == form_data.username
        ).first()
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas"
            )
        
        # Verificar si está bloqueado
        if admin.bloqueado_hasta and admin.bloqueado_hasta > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cuenta bloqueada temporalmente. Intenta en 15 minutos."
            )
        
        # Verificar contraseña
        if not auth_servicio.verify_password(form_data.password, admin.hashed_password):
            # Incrementar intentos fallidos
            admin.intentos_fallidos = (admin.intentos_fallidos or 0) + 1
            db.commit()
            
            if admin.intentos_fallidos >= 3:
                # Bloquear por 15 minutos
                admin.bloqueado_hasta = datetime.utcnow() + timedelta(minutes=15)
                admin.intentos_fallidos = 0
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Has fallado 3 veces. Cuenta bloqueada por 15 min."
                )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Contraseña incorrecta. Intento {admin.intentos_fallidos}/3"
            )
        
        # Éxito: resetear intentos
        admin.intentos_fallidos = 0
        admin.bloqueado_hasta = None
        db.commit()
        
        # Generar token
        access_token = auth_servicio.create_access_token(data={"sub": admin.username})
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/request-registration-code")
async def request_registration_code(
    request_data: RegistrationRequest,
    db: Session = Depends(get_db)
):
    """Solicitar código de verificación para registro"""
    try:
        # Verificar email autorizado
        if request_data.email.lower() != auth_servicio.ALLOWED_ADMIN_EMAIL.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Este correo electrónico no está autorizado para registrarse."
            )
        
        # Generar código y expiración
        code = str(random.randint(100000, 999999))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        # Guardar en la base de datos (UPSERT)
        pending = db.query(PendingRegistration).filter(
            PendingRegistration.email == request_data.email.lower()
        ).first()
        
        if pending:
            pending.verification_code = code
            pending.expires_at = expires_at
        else:
            pending = PendingRegistration(
                email=request_data.email.lower(),
                verification_code=code,
                expires_at=expires_at
            )
            db.add(pending)
        
        db.commit()
        
        # Enviar correo
        await send_verification_code(request_data.email, code)
        
        return {"mensaje": "Se ha enviado un código de verificación a tu correo."}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en request registration: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/complete-registration")
async def complete_registration(
    completion_data: RegistrationCompletion,
    db: Session = Depends(get_db)
):
    """Completar registro de administrador"""
    try:
        email_lower = completion_data.email.lower()
        
        # Verificar email autorizado
        if email_lower != auth_servicio.ALLOWED_ADMIN_EMAIL.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Este correo no está autorizado."
            )
        
        # Validar fortaleza de contraseña
        password = completion_data.password
        errores_pass = []
        if len(password) < 8:
            errores_pass.append("Mínimo 8 caracteres")
        if not re.search(r"[A-Z]", password):
            errores_pass.append("Una mayúscula")
        if not re.search(r"\d", password):
            errores_pass.append("Un número")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errores_pass.append("Un símbolo (!@#$...)")
        
        if errores_pass:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La contraseña es débil. Falta: {', '.join(errores_pass)}"
            )
        
        # Verificar código pendiente
        pending = db.query(PendingRegistration).filter(
            PendingRegistration.email == email_lower
        ).first()
        
        if not pending:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solicitud no encontrada."
            )
        
        if pending.verification_code != completion_data.verification_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código incorrecto."
            )
        
        if pending.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código expirado."
            )
        
        # Hashear contraseña
        hashed_password = auth_servicio.get_password_hash(password)
        
        # Crear o actualizar administrador
        admin = db.query(Administrador).filter(
            Administrador.username == email_lower
        ).first()
        
        if admin:
            admin.hashed_password = hashed_password
            mensaje = "¡Contraseña actualizada correctamente!"
        else:
            admin = Administrador(
                id=uuid.uuid4(),
                username=email_lower,
                email=email_lower,
                hashed_password=hashed_password,
                intentos_fallidos=0
            )
            db.add(admin)
            mensaje = "¡Administrador registrado con éxito!"
        
        # Eliminar registro pendiente
        db.delete(pending)
        db.commit()
        
        return {"mensaje": mensaje}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en complete registration: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )