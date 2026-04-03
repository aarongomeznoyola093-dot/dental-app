from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cita, Paciente
from app.servicios.auth_servicio import get_current_user
import uuid
from datetime import datetime, timedelta
import logging

router = APIRouter(
    prefix="/citas",
    tags=["Citas"],
    dependencies=[Depends(get_current_user)]
)

# ==========================================================
# REGISTRAR CITA
# ==========================================================
@router.post("/")
async def registrar_cita(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        
        # Limpiar el ID del paciente (eliminar espacios, tabs, saltos de línea)
        id_paciente = data.get("id_paciente", "").strip()
        
        # Validar que sea un UUID válido
        try:
            import uuid
            uuid.UUID(id_paciente)
        except:
            raise HTTPException(status_code=400, detail=f"ID de paciente inválido: {id_paciente}")
        
        try:
            fecha_hora_obj = datetime.fromisoformat(data["fecha_hora"])
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Formato de fecha y hora inválido.")
        
        # Crear la cita
        nueva_cita = Cita(
            id=str(uuid.uuid4()),
            id_paciente=id_paciente,
            fecha_hora=fecha_hora_obj,
            motivo=data["motivo"],
            estado=data.get("estado", "programada")
        )
        
        db.add(nueva_cita)
        db.commit()
        
        return {"mensaje": "Cita registrada correctamente", "id": nueva_cita.id}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al registrar cita: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================================
# OBTENER TODAS LAS CITAS
# ==========================================================
@router.get("/")
def obtener_citas(db: Session = Depends(get_db)):

    citas = db.query(Cita).all()

    resultado = []

    for c in citas:
        resultado.append({
            "id_cita": c.id,
            "id_paciente": c.id_paciente,
            "fecha_hora": c.fecha_hora.isoformat(),
            "motivo": c.motivo,
            "estado": c.estado
        })

    return resultado


# ==========================================================
# CITAS PARA CALENDARIO
# ==========================================================
@router.get("/calendario")
def obtener_citas_calendario(db: Session = Depends(get_db)):

    citas = db.query(Cita).filter(Cita.estado == "programada").all()
    pacientes = db.query(Paciente).all()

    mapa_pacientes = {
        str(p.id): f"{p.nombre} {p.apellido_pat}"
        for p in pacientes
    }

    eventos = []

    for cita in citas:
        nombre_paciente = mapa_pacientes.get(str(cita.id_paciente), "Paciente")

        inicio = cita.fecha_hora
        fin = inicio + timedelta(hours=1)

        eventos.append({
            "id": str(cita.id),
            "title": f"{nombre_paciente} ({cita.motivo})",
            "start": inicio.isoformat(),
            "end": fin.isoformat()
        })

    return eventos


# ==========================================================
# ACTUALIZAR CITA
# ==========================================================
@router.put("/{id_cita}")
async def actualizar_cita(id_cita: str, request: Request, db: Session = Depends(get_db)):

    data = await request.json()

    cita = db.query(Cita).filter(Cita.id == id_cita).first()

    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    cita.fecha_hora = datetime.fromisoformat(data["fecha_hora"])
    cita.motivo = data["motivo"]
    cita.estado = data["estado"]

    db.commit()

    return {"mensaje": "Cita actualizada correctamente"}


# ==========================================================
# ELIMINAR CITA
# ==========================================================
@router.delete("/{id_cita}")
def eliminar_cita(id_cita: str, db: Session = Depends(get_db)):

    cita = db.query(Cita).filter(Cita.id == id_cita).first()

    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    db.delete(cita)
    db.commit()

    return {"mensaje": "Cita eliminada correctamente"}
# ==========================================================
# ASIGNAR TRATAMIENTO A CITA
# ==========================================================
@router.post("/cita-tratamiento")
async def asignar_tratamiento_a_cita(
    request: Request,
    db: Session = Depends(get_db)
):
    """Asigna un tratamiento a una cita específica"""
    try:
        data = await request.json()
        
        # Importar modelos necesarios
        from app.models import CitaTratamiento
        
        # Crear la relación cita-tratamiento
        nueva_relacion = CitaTratamiento(
            id_cita=data["id_cita"],
            id_tratamiento=data["id_tratamiento"],
            observaciones=data.get("observaciones", ""),
            resultado=data.get("resultado", "")
        )
        
        db.add(nueva_relacion)
        db.commit()
        
        return {"mensaje": "Tratamiento asignado a la cita correctamente"}
        
    except Exception as e:
        print(f"Error al asignar tratamiento: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
# ==========================================================
# OBTENER CITA POR ID (PARA EDITAR)
# ==========================================================
@router.get("/{id_cita}")
async def obtener_cita(id_cita: str, db: Session = Depends(get_db)):
    """Obtiene una cita específica por su ID"""
    from app.models import Cita
    
    cita = db.query(Cita).filter(Cita.id == id_cita).first()
    
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    return {
        "id_cita": str(cita.id),
        "id_paciente": str(cita.id_paciente),
        "fecha_hora": cita.fecha_hora.isoformat() if cita.fecha_hora else None,
        "motivo": cita.motivo,
        "estado": cita.estado
    }