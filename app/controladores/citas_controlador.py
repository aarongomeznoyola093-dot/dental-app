from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cita, Paciente
from app.servicios.auth_servicio import get_current_user
import uuid
import logging
from datetime import datetime, timedelta

router = APIRouter(prefix="/citas", tags=["Citas"], dependencies=[Depends(get_current_user)])

@router.post("/")
async def registrar_cita(data: Request, force: bool = Query(False), db: Session = Depends(get_db)):
    try:
        body = await data.json()
        try:
            fecha_hora_obj = datetime.fromisoformat(body["fecha_hora"])
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Formato de fecha y hora inválido.")
        
        if not force:
            # Verificar si ya existe una cita en ese horario
            cita_existente = db.query(Cita).filter(Cita.fecha_hora == fecha_hora_obj).first()
            if cita_existente:
                raise HTTPException(
                    status_code=409, 
                    detail="¡Conflicto! Ya existe una cita en ese horario. ¿Desea registrarla de todos modos?"
                )
        
        # Crear nueva cita
        nueva_cita = Cita(
            id=uuid.UUID(body["id_cita"]),
            id_paciente=uuid.UUID(body["id_paciente"]),
            fecha_hora=fecha_hora_obj,
            motivo=body["motivo"],
            estado=body["estado"]
        )
        db.add(nueva_cita)
        db.commit()
        
        return {"mensaje": "Cita guardada correctamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error al procesar la cita: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/calendario")
async def obtener_citas_calendario(db: Session = Depends(get_db)):
    try:
        # Obtener todos los pacientes
        pacientes = db.query(Paciente).all()
        pacientes_map = {str(p.id): f"{p.nombre} {p.apellido_pat}" for p in pacientes}
        
        # Obtener todas las citas programadas
        citas = db.query(Cita).filter(Cita.estado == "programada").all()
        
        eventos = []
        for cita in citas:
            paciente_nombre = pacientes_map.get(str(cita.id_paciente), "Paciente Desconocido")
            titulo_evento = f"{paciente_nombre} ({cita.motivo})"
            
            start_time = cita.fecha_hora
            end_time = start_time + timedelta(hours=1)
            eventos.append({
                "id": str(cita.id),
                "title": titulo_evento,
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            })
        return eventos
        
    except Exception as e:
        logging.error(f"Error al obtener citas para calendario: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")