from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import logging
from fastapi_mail import ConnectionConfig
import os

from app.database import engine, Base
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.limiter import limiter

# Importamos los controladores
from app.controladores import admin_controlador
from app.controladores import pacientes_controlador 
from app.controladores import citas_controlador
from app.controladores import relaciones_pagos_controlador
from app.controladores import tratamiento_controlador
from app.controladores import reportes_controlador
from app.controladores import pagos_controlador

logging.basicConfig(level=logging.INFO)

# Configuración de email
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

if MAIL_USERNAME and MAIL_PASSWORD:
    conf = ConnectionConfig(
        MAIL_USERNAME=MAIL_USERNAME,
        MAIL_PASSWORD=MAIL_PASSWORD,
        MAIL_FROM=MAIL_USERNAME,
        MAIL_PORT=587,
        MAIL_SERVER="smtp.gmail.com",
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False
    )
else:
    conf = None

app = FastAPI()

# ========== RATE LIMIT ==========
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ========== PROMETHEUS ==========
Instrumentator().instrument(app).expose(app)

# ========== CREAR TABLAS ==========
@app.on_event("startup")
def on_startup():
    print("--- INICIANDO APLICACIÓN ---")
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Tablas creadas correctamente")
    except Exception as e:
        print("✗ Error creando tablas:", e)

@app.on_event("shutdown")
def on_shutdown():
    print("✓ Cerrando conexiones...")

# ========== ROUTERS ==========
app.include_router(admin_controlador.router)
app.include_router(pacientes_controlador.router)
app.include_router(citas_controlador.router)
app.include_router(relaciones_pagos_controlador.router)
app.include_router(tratamiento_controlador.router)
app.include_router(reportes_controlador.router)
app.include_router(pagos_controlador.router)

# ========== ARCHIVOS ESTÁTICOS ==========
app.mount("/app", StaticFiles(directory="static"), name="static")

# ========== REDIRECCIÓN ==========
@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/app/login.html")