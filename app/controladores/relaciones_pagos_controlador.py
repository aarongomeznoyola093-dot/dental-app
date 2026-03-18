
from fastapi import APIRouter, Depends, Request, HTTPException
import uuid
from datetime import date
from decimal import Decimal  
import logging


from app.db_session import get_session
from app.servicios.auth_servicio import get_current_user 


router = APIRouter(
    tags=["Pagos y Relaciones"],  
    dependencies=[Depends(get_current_user)]  
)

session = get_session()

@router.post("/cita-tratamiento")
async def registrar_cita_tratamiento(data: Request):
    try:
        body = await data.json()
        query = """
        INSERT INTO cita_tratamiento (id_paciente, id_cita, id_tratamiento, observaciones, resultado)
        VALUES (%s, %s, %s, %s, %s)
        """
        session.execute(query, (
            uuid.UUID(body["id_paciente"]), uuid.UUID(body["id_cita"]),
            uuid.UUID(body["id_tratamiento"]), body["observaciones"], body["resultado"]
        ))
        return {"mensaje": "Tratamiento asignado a la cita correctamente"}
    except Exception as e:
        logging.error(f" Error al procesar cita-tratamiento: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/pago")
async def registrar_pago(data: Request):
    try:
        body = await data.json()
        query = """
        INSERT INTO pago (id_paciente, id_cita, id_pago, monto, fecha_pago, metodo_pago)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        session.execute(query, (
            uuid.UUID(body["id_paciente"]), uuid.UUID(body["id_cita"]),
            uuid.UUID(body["id_pago"]), Decimal(body["monto"]),
            date.fromisoformat(body["fecha_pago"]), body["metodo_pago"]
        ))
        return {"mensaje": "Pago registrado correctamente"}
    except Exception as e:
        logging.error(f" Error al procesar el pago: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.put("/pago")
async def actualizar_pago(data: Request):
    try:
        body = await data.json()
        query = """
        UPDATE pago SET monto = %s, fecha_pago = %s, metodo_pago = %s
        WHERE id_paciente = %s AND id_cita = %s AND id_pago = %s
        """
        session.execute(query, (
            Decimal(body["monto"]), date.fromisoformat(body["fecha_pago"]), body["metodo_pago"],
            uuid.UUID(body["id_paciente"]), uuid.UUID(body["id_cita"]), uuid.UUID(body["id_pago"])
        ))
        return {"mensaje": "Pago actualizado correctamente"}
    except Exception as e:
        logging.error(f" Error al actualizar el pago: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.delete("/pago")
async def eliminar_pago(data: Request):
    try:
        body = await data.json()
        query = "DELETE FROM pago WHERE id_paciente = %s AND id_cita = %s AND id_pago = %s"
        session.execute(query, [
            uuid.UUID(body["id_paciente"]), uuid.UUID(body["id_cita"]), uuid.UUID(body["id_pago"])
        ])
        return {"mensaje": "Pago eliminado correctamente"}
    except Exception as e:
        logging.error(f" Error al eliminar el pago: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/abono")
async def registrar_abono(data: Request):
    try:
        body = await data.json()
        id_tratamiento = uuid.UUID(body["id_tratamiento"]) if body.get("id_tratamiento") else None
        query = """
        INSERT INTO abono (id_paciente, id_abono, id_tratamiento, fecha_abono, monto_abonado, saldo_restante, estado)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        session.execute(query, (
            uuid.UUID(body["id_paciente"]), uuid.UUID(body["id_abono"]),
            id_tratamiento, date.fromisoformat(body["fecha_abono"]),
            Decimal(body["monto_abonado"]), Decimal(body["saldo_restante"]),
            body["estado"]
        ))
        return {"mensaje": "Abono registrado correctamente"}
    except Exception as e:
        logging.error(f" Error al procesar el abono: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.put("/abono")
async def actualizar_abono(data: Request):
    try:
        body = await data.json()
        id_tratamiento = uuid.UUID(body["id_tratamiento"]) if body.get("id_tratamiento") else None
        query = """
        UPDATE abono SET id_tratamiento = %s, fecha_abono = %s, monto_abonado = %s, saldo_restante = %s, estado = %s
        WHERE id_paciente = %s AND id_abono = %s
        """
        session.execute(query, (
            id_tratamiento, date.fromisoformat(body["fecha_abono"]), Decimal(body["monto_abonado"]),
            Decimal(body["saldo_restante"]), body["estado"],
            uuid.UUID(body["id_paciente"]), uuid.UUID(body["id_abono"])
        ))
        return {"mensaje": "Abono actualizado correctamente"}
    except Exception as e:
        logging.error(f" Error al actualizar el abono: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.delete("/abono")
async def eliminar_abono(data: Request):
    try:
        body = await data.json()
        query = "DELETE FROM abono WHERE id_paciente = %s AND id_abono = %s"
        session.execute(query, [
            uuid.UUID(body["id_paciente"]), uuid.UUID(body["id_abono"])
        ])
        return {"mensaje": "Abono eliminado correctamente"}
    except Exception as e:
        logging.error(f" Error al eliminar el abono: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")