from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Paciente
from app.servicios.auth_servicio import get_current_user
import uuid
from datetime import datetime

router = APIRouter(
    prefix="/pacientes",
    tags=["Pacientes"],
    dependencies=[Depends(get_current_user)]
)

# ==========================================================
# OBTENER PACIENTES
# ==========================================================
@router.get("/")
def obtener_pacientes(db: Session = Depends(get_db)):

    pacientes = db.query(Paciente).all()

    resultado = []

    for p in pacientes:
        resultado.append({
            "id_paciente": p.id,
            "nombre": p.nombre,
            "apellido_pat": p.apellido_pat,
            "apellido_mat": p.apellido_mat,
            "fecha_nacimiento": str(p.fecha_nacimiento) if p.fecha_nacimiento else None,
            "edad": p.edad,
            "telefono": p.telefono,
            "enfermedades": p.enfermedades or [],
            "medicamentos": p.medicamentos or [],
            "alergias": p.alergias or []
        })

    return resultado




# ==========================================================
# REGISTRAR PACIENTE
# ==========================================================
@router.post("/")
async def registrar_paciente(request: Request, db: Session = Depends(get_db)):

    data = await request.json()

    fecha_nacimiento = None
    if data.get("fecha_nacimiento"):
        fecha_nacimiento = datetime.strptime(data["fecha_nacimiento"], "%Y-%m-%d").date()

    nuevo_paciente = Paciente(
        id=str(uuid.uuid4()),
        nombre=data["nombre"],
        apellido_pat=data["apellido_pat"],
        apellido_mat=data.get("apellido_mat"),
        fecha_nacimiento=fecha_nacimiento,
        edad=data.get("edad"),
        telefono=data.get("telefono"),
        enfermedades=data.get("enfermedades", []),
        medicamentos=data.get("medicamentos", []),
        alergias=data.get("alergias", [])
    )

    db.add(nuevo_paciente)
    db.commit()
    db.refresh(nuevo_paciente)

    return {"mensaje": "Paciente registrado correctamente"}


# ==========================================================
# ACTUALIZAR PACIENTE
# ==========================================================
@router.put("/{id_paciente}")
async def actualizar_paciente(id_paciente: str, request: Request, db: Session = Depends(get_db)):

    data = await request.json()

    paciente = db.query(Paciente).filter(Paciente.id == id_paciente).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    if data.get("fecha_nacimiento"):
        paciente.fecha_nacimiento = datetime.strptime(data["fecha_nacimiento"], "%Y-%m-%d").date()

    paciente.nombre = data["nombre"]
    paciente.apellido_pat = data["apellido_pat"]
    paciente.apellido_mat = data.get("apellido_mat")
    paciente.edad = data.get("edad")
    paciente.telefono = data.get("telefono")
    paciente.enfermedades = data.get("enfermedades", [])
    paciente.medicamentos = data.get("medicamentos", [])
    paciente.alergias = data.get("alergias", [])

    db.commit()

    return {"mensaje": "Paciente actualizado correctamente"}


# ==========================================================
# ELIMINAR PACIENTE
# ==========================================================
@router.delete("/{id_paciente}")
def eliminar_paciente(id_paciente: str, db: Session = Depends(get_db)):

    paciente = db.query(Paciente).filter(Paciente.id == id_paciente).first()

    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    db.delete(paciente)
    db.commit()

    return {"mensaje": "Paciente eliminado correctamente"}
# ==========================================================
# OBTENER HISTORIAL DEL PACIENTE
# ==========================================================
@router.get("/{id_paciente}/historial")
def obtener_historial_paciente(
    id_paciente: str,
    db: Session = Depends(get_db)
):
    """Obtiene el historial completo de un paciente (citas, tratamientos, pagos, abonos)"""
    
    # Buscar paciente
    paciente = db.query(Paciente).filter(Paciente.id == id_paciente).first()
    
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    # Importar modelos adicionales (si están definidos)
    from app.models import Cita, Tratamiento, CitaTratamiento, Pago, Abono
    
    # Buscar citas del paciente
    citas = db.query(Cita).filter(Cita.id_paciente == id_paciente).all()
    
    # Formatear citas con sus tratamientos y pagos
    citas_detalladas = []
    for cita in citas:
        # Buscar tratamientos de esta cita
        tratamientos_cita = db.query(CitaTratamiento).filter(
            CitaTratamiento.id_cita == cita.id
        ).all()
        
        # Buscar pagos de esta cita
        pagos_cita = db.query(Pago).filter(Pago.id_cita == cita.id).all()
        
        citas_detalladas.append({
            "id_cita": str(cita.id),
            "fecha_hora": str(cita.fecha_hora),
            "motivo": cita.motivo,
            "estado": cita.estado,
            "tratamientos": [
                {
                    "id_tratamiento": str(ct.id_tratamiento),
                    "observaciones": ct.observaciones,
                    "resultado": ct.resultado
                }
                for ct in tratamientos_cita
            ],
            "pagos": [
                {
                    "id_pago": str(p.id),
                    "monto": p.monto,
                    "fecha_pago": str(p.fecha_pago),
                    "metodo_pago": p.metodo_pago
                }
                for p in pagos_cita
            ]
        })
    
    # Buscar abonos del paciente
    abonos = db.query(Abono).filter(Abono.id_paciente == id_paciente).all()
    abonos_lista = [
        {
            "id_abono": str(a.id),
            "fecha_abono": str(a.fecha_abono),
            "monto_abonado": a.monto_abonado,
            "saldo_restante": a.saldo_restante,
            "estado": a.estado,
            "id_tratamiento": str(a.id_tratamiento) if a.id_tratamiento else None
        }
        for a in abonos
    ]
    
    # Formatear respuesta
    historial = {
        "paciente": {
            "id_paciente": str(paciente.id),
            "nombre": paciente.nombre,
            "apellido_pat": paciente.apellido_pat,
            "apellido_mat": paciente.apellido_mat,
            "fecha_nacimiento": str(paciente.fecha_nacimiento) if paciente.fecha_nacimiento else None,
            "edad": paciente.edad,
            "telefono": paciente.telefono,
            "enfermedades": paciente.enfermedades or [],
            "medicamentos": paciente.medicamentos or [],
            "alergias": paciente.alergias or []
        },
        "citas_detalladas": citas_detalladas,
        "abonos": abonos_lista
    }
    
    return historial