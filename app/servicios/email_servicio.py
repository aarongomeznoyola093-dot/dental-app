
from fastapi_mail import FastMail, MessageSchema
from app.config import conf 
import logging

async def send_verification_code(email_to: str, code: str):
    """
    Envía un correo de verificación real al usuario.
    """
    if conf is None:
        logging.error("Configuración de correo no cargada. No se puede enviar el código.")
        raise Exception("El servidor de correo no está configurado.")

    body = f"""
    <p>Hola,</p>
    <p>Tu código de verificación para Dental Criss es:</p>
    <h2 style="color: #6a5acd; text-align: center;">{code}</h2>
    <p>Este código expira en 10 minutos.</p>
    """

    message = MessageSchema(
        subject="Dental Criss - Tu Código de Verificación",
        recipients=[email_to],
        body=body,
        subtype="html"
    )

    try:
        fm = FastMail(conf)
        await fm.send_message(message)
        logging.info(f"Correo de verificación real enviado a {email_to}")
    except Exception as e:
        logging.error(f"¡FALLO AL ENVIAR CORREO!: {e}")
        raise e