from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jwt import PyJWTError 
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional



ALLOWED_ADMIN_EMAIL = "aarongomeznoyola093@gmail.com"

SECRE = "G5GhNYx6hUJ8A7uD4NQ6Gf3lR4v2aPZ4T9qkl2DFg9o" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120 #


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que la contraseña simple coincida con la encriptada."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera un hash (encriptado) de una contraseña."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea un nuevo Token de Acceso (JWT)."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    
    # Generar token usando PyJWT
    encoded_jwt = jwt.encode(to_encode, SECRE, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    Dependencia de FastAPI para proteger rutas.
    Decodifica el token y devuelve el username.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodificar token usando PyJWT
        payload = jwt.decode(token, SECRE, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except PyJWTError: 
        raise credentials_exception

    return username