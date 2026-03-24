from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from app.db_session import get_db_session
from app.servicios import auth_servicio
from datetime import datetime, timedelta
import uuid
import logging

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    session = get_db_session()
    
    # Buscar admin por username
    query = "SELECT * FROM administrador WHERE username = %s ALLOW FILTERING"
    result = session.execute(query, [form_data.username])
    admin = result.one()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    
    # Verificar contraseña
    if not auth_servicio.verify_password(form_data.password, admin['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    
    # Generar token
    access_token = auth_servicio.create_access_token(
        data={"sub": admin['username']}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/request-registration-code")
async def request_registration_code(request: Request):
    # Tu código existente para solicitar código de registro
    pass

@router.post("/complete-registration")
async def complete_registration(request: Request):
    # Tu código existente para completar registro
    pass