
from fastapi_mail import ConnectionConfig
import os
import logging
from dotenv import load_dotenv  


load_dotenv() 

MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

print(f"Correo: {MAIL_USERNAME}")
if MAIL_PASSWORD:
    print(f"Contraseña: {MAIL_PASSWORD[:4]}... [OCULTA]")
else:
    print("Contraseña: None")
print("-------------------------------------\n\n")

conf = None
if not MAIL_USERNAME or not MAIL_PASSWORD:
    logging.warning("--- ¡ADVERTENCIA DE CORREO! ---")
    logging.warning("Las variables 'MAIL_USERNAME' o 'MAIL_PASSWORD' no están configuradas.")
    logging.warning("El registro de administrador fallará.")
else:
    conf = ConnectionConfig(
        MAIL_USERNAME = MAIL_USERNAME,
        MAIL_PASSWORD = MAIL_PASSWORD,
        MAIL_FROM = MAIL_USERNAME,
        MAIL_PORT = 465,
        MAIL_SERVER = "smtp.gmail.com",
        MAIL_STARTTLS = False,
        MAIL_SSL_TLS = True
    )