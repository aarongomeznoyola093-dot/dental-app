from fastapi import APIRouter, Depends, HTTPException, status, Request # <-- IMPORTANTE: Request
from fastapi.security import OAuth2PasswordRequestForm
import uuid
import logging
from app.servicios import email_servicio
from app.servicios.auth_servicio import ALLOWED_ADMIN_EMAIL
from app.db_session import get_session
from app.servicios import auth_servicio
import re
import random
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, EmailStr

from app.limiter import limiter 

router = APIRouter(prefix="/admin", tags=["Admin"])

# --- LOGIN ---
@router.post("/token")
@limiter.limit("5/minute") 
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()): 
    
    session = get_session()
    
    if session is None:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")

    # 2. Buscar usuario
    user_row = session.execute("SELECT * FROM administrador WHERE username = %s ALLOW FILTERING", [form_data.username]).one()

    if not user_row:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    # 3. Verificar si está BLOQUEADO
    bloqueado_hasta = user_row.get('bloqueado_hasta')
    if bloqueado_hasta and bloqueado_hasta > datetime.utcnow():
        raise HTTPException(status_code=400, detail="Cuenta bloqueada temporalmente. Intenta en 15 minutos.")

    # 4. Verificar Contraseña
    if not auth_servicio.verify_password(form_data.password, user_row['hashed_password']):
        
        intentos = (user_row.get('intentos_fallidos') or 0) + 1
        admin_id = user_row['id_admin']
        
        if intentos >= 3:
            # Bloquear por 15 minutos
            bloqueo = datetime.utcnow() + timedelta(minutes=15)
            session.execute("UPDATE administrador SET intentos_fallidos = 0, bloqueado_hasta = %s WHERE id_admin = %s", (bloqueo, admin_id))
            raise HTTPException(status_code=400, detail="Has fallado 3 veces. Cuenta bloqueada por 15 min.")
        else:
            session.execute("UPDATE administrador SET intentos_fallidos = %s WHERE id_admin = %s", (intentos, admin_id))
            raise HTTPException(status_code=401, detail=f"Contraseña incorrecta. Intento {intentos}/3")

    if user_row.get('intentos_fallidos', 0) != 0:
        session.execute("UPDATE administrador SET intentos_fallidos = 0, bloqueado_hasta = null WHERE id_admin = %s", [user_row['id_admin']])
    
    # Generar Token
    access_token = auth_servicio.create_access_token(data={"sub": user_row['username']})
    return {"access_token": access_token, "token_type": "bearer"}

class RegistrationRequest(BaseModel):
    email: EmailStr

class RegistrationCompletion(BaseModel):
    email: EmailStr
    password: str
    verification_code: str



@router.post("/request-registration-code")
async def request_registration_code(request_data: RegistrationRequest):
    session = get_session()
    if session is None:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")

    if request_data.email.lower() != ALLOWED_ADMIN_EMAIL.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este correo electrónico no está autorizado para registrarse."
        )

    
    code = str(random.randint(100000, 999999))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    
    query = "INSERT INTO pending_registration (email, verification_code, expires_at) VALUES (%s, %s, %s)"
    session.execute(query, (request_data.email.lower(), code, expires_at))

    # Enviar correo
    await email_servicio.send_verification_code(request_data.email, code)

    return {"mensaje": "Se ha enviado un código de verificación a tu correo."}



@router.post("/complete-registration")
async def complete_registration(completion_data: RegistrationCompletion):
    session = get_session()
    if session is None:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    
    email_lower = completion_data.email.lower()
    if email_lower != ALLOWED_ADMIN_EMAIL.lower():
        raise HTTPException(status_code=403, detail="Este correo no está autorizado.")

    
    password = completion_data.password
    errores_pass = []
    if len(password) < 8: errores_pass.append("Mínimo 8 caracteres")
    if not re.search(r"[A-Z]", password): errores_pass.append("Una mayúscula")
    if not re.search(r"\d", password): errores_pass.append("Un número")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): errores_pass.append("Un símbolo (!@#$...)")
    
    if errores_pass:
        raise HTTPException(status_code=400, detail=f"La contraseña es débil. Falta: {', '.join(errores_pass)}")

    
    query = "SELECT verification_code, expires_at FROM pending_registration WHERE email = %s"
    pending_reg = session.execute(query, [email_lower]).one()

    if not pending_reg: 
        raise HTTPException(status_code=400, detail="Solicitud no encontrada.")
    
    if pending_reg['verification_code'] != completion_data.verification_code: 
        raise HTTPException(status_code=400, detail="Código incorrecto.")
    
    if pending_reg['expires_at'] < datetime.utcnow(): 
        raise HTTPException(status_code=400, detail="Código expirado.")


    hashed_password = auth_servicio.get_password_hash(password)

    
    check_admin = session.execute("SELECT id_admin FROM administrador WHERE username = %s ALLOW FILTERING", [email_lower]).one()

    if check_admin:
        session.execute("UPDATE administrador SET hashed_password = %s WHERE id_admin = %s", (hashed_password, check_admin['id_admin']))
        mensaje = "¡Contraseña actualizada correctamente!"
    else:
        session.execute("INSERT INTO administrador (id_admin, username, hashed_password) VALUES (%s, %s, %s)", (uuid.uuid4(), email_lower, hashed_password))
        mensaje = "¡Administrador registrado con éxito!"

    session.execute("DELETE FROM pending_registration WHERE email = %s", [email_lower])
    return {"mensaje": mensaje}