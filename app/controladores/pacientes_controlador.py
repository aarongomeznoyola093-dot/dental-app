from fastapi import APIRouter, Depends, HTTPException, Request
from app.db_session import get_session
from app.servicios.auth_servicio import get_current_user
import uuid
import logging
from datetime import date, datetime

router = APIRouter(
    prefix="/paciente", 
    tags=["Pacientes"], 
    dependencies=[Depends(get_current_user)]
)

# --- UTILERÍA PARA FECHAS ---
def convertir_fecha(fecha_obj):
    """Convierte fechas de Cassandra a string para que el JSON no falle"""
    if not fecha_obj:
        return None
    return str(fecha_obj)

# --- 1. OBTENER TODOS LOS PACIENTES 
@router.get("/") 
async def obtener_pacientes():
    session = get_session()
    if session is None:
        raise HTTPException(status_code=500, detail="Error de conexión BD")
    
    try:
        rows = session.execute("SELECT * FROM paciente")
        pacientes = []
        
        for row in rows:
            paciente = {
                "id_paciente": str(row['id_paciente']),
                "nombre": row['nombre'],
                "apellido_pat": row.get('apellido_pat', ''),
                "apellido_mat": row.get('apellido_mat', ''),
                "fecha_nacimiento": convertir_fecha(row.get('fecha_nacimiento')),
                "edad": row.get('edad', 0),
                "telefono": row.get('telefono', ''),
                # Convertimos a lista para el JSON
                "enfermedades": list(row.get('enfermedades', [])),
                "medicamentos": list(row.get('medicamentos', [])),
                "alergias": list(row.get('alergias', []))
            }
            pacientes.append(paciente)
            
        return pacientes

    except Exception as e:
        logging.error(f"Error al listar pacientes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id_paciente}/historial")
async def obtener_historial_paciente(id_paciente: uuid.UUID):
    session = get_session()
    if session is None: raise HTTPException(status_code=500, detail="Error BD")
    
    try:

        row_p = session.execute("SELECT * FROM paciente WHERE id_paciente = %s", [id_paciente]).one()
        if not row_p:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")
            
        paciente = {
            "id_paciente": str(row_p['id_paciente']),
            "nombre": row_p['nombre'],
            "apellido_pat": row_p.get('apellido_pat', ''),
            "apellido_mat": row_p.get('apellido_mat', ''),
            "fecha_nacimiento": convertir_fecha(row_p.get('fecha_nacimiento')),
            "edad": row_p.get('edad'),
            "telefono": row_p.get('telefono'),
            "enfermedades": list(row_p.get('enfermedades', [])),
            "medicamentos": list(row_p.get('medicamentos', [])),
            "alergias": list(row_p.get('alergias', []))
        }

        
        citas = []
        rows_c = session.execute("SELECT * FROM cita WHERE id_paciente = %s ALLOW FILTERING", [id_paciente])
        
        for rc in rows_c:
            id_cita = rc['id_cita']
            
            
            tratamientos_cita = []
            rows_ct = session.execute("SELECT * FROM cita_tratamiento WHERE id_cita = %s ALLOW FILTERING", [id_cita])
            for rct in rows_ct:
                tratamientos_cita.append({
                    "id_tratamiento": str(rct['id_tratamiento']),
                    "observaciones": rct.get('observaciones', ''),
                    "resultado": rct.get('resultado', '')
                })

            
            pagos_cita = []
            rows_pago = session.execute("SELECT * FROM pago WHERE id_cita = %s ALLOW FILTERING", [id_cita])
            for rp in rows_pago:
                pagos_cita.append({
                    "id_pago": str(rp['id_pago']),
                    "monto": float(rp['monto']) if rp['monto'] else 0.0,
                    "fecha_pago": convertir_fecha(rp['fecha_pago']),
                    "metodo_pago": rp.get('metodo_pago', '')
                })

            citas.append({
                "id_cita": str(id_cita),
                "fecha_hora": str(rc['fecha_hora']),
                "motivo": rc['motivo'],
                "estado": rc['estado'],
                "tratamientos": tratamientos_cita,
                "pagos": pagos_cita
            })

        
        abonos = []
        rows_a = session.execute("SELECT * FROM abono WHERE id_paciente = %s ALLOW FILTERING", [id_paciente])
        for ra in rows_a:
            abonos.append({
                "id_abono": str(ra['id_abono']),
                "fecha_abono": convertir_fecha(ra['fecha_abono']),
                "monto_abonado": float(ra['monto_abonado']),
                "saldo_restante": float(ra['saldo_restante']),
                "estado": ra.get('estado', '')
            })

        return {
            "paciente": paciente,
            "citas_detalladas": citas,
            "abonos": abonos
        }

    except Exception as e:
        logging.error(f"Error historial: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def registrar_paciente(data: Request):
    session = get_session()
    if session is None: raise HTTPException(status_code=500, detail="Error BD")

    try:
        body = await data.json()
        fecha_nac = None
        if body.get("fecha_nacimiento"):
            fecha_nac = datetime.strptime(body["fecha_nacimiento"], "%Y-%m-%d").date()

        query = """
        INSERT INTO paciente (id_paciente, nombre, apellido_pat, apellido_mat, fecha_nacimiento, edad, telefono, enfermedades, medicamentos, alergias)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        session.execute(query, (
            uuid.UUID(body["id_paciente"]),
            body["nombre"],
            body.get("apellido_pat", ""),
            body.get("apellido_mat", ""),
            fecha_nac,
            int(body["edad"]),
            body.get("telefono", ""),
            
            list(body.get("enfermedades", [])), 
            list(body.get("medicamentos", [])),
            list(body.get("alergias", []))
        ))
        return {"mensaje": "Paciente registrado correctamente"}
    except Exception as e:
        logging.error(f"Error registro paciente: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{id_paciente}")
async def actualizar_paciente(id_paciente: uuid.UUID, data: Request):
    session = get_session()
    if session is None: raise HTTPException(status_code=500, detail="Error BD")

    try:
        body = await data.json()
        fecha_nac = None
        if body.get("fecha_nacimiento"):
            fecha_nac = datetime.strptime(body["fecha_nacimiento"], "%Y-%m-%d").date()

        query = """
        UPDATE paciente SET nombre=%s, apellido_pat=%s, apellido_mat=%s, fecha_nacimiento=%s, edad=%s, telefono=%s, enfermedades=%s, medicamentos=%s, alergias=%s
        WHERE id_paciente=%s
        """
        session.execute(query, (
            body["nombre"],
            body.get("apellido_pat", ""),
            body.get("apellido_mat", ""),
            fecha_nac,
            int(body["edad"]),
            body.get("telefono", ""),
            
            list(body.get("enfermedades", [])),
            list(body.get("medicamentos", [])),
            list(body.get("alergias", [])),
            id_paciente
        ))
        return {"mensaje": "Paciente actualizado correctamente"}
    except Exception as e:
        logging.error(f"Error actualizar paciente: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{id_paciente}")
async def eliminar_paciente(id_paciente: uuid.UUID):
    session = get_session()
    if session is None: raise HTTPException(status_code=500, detail="Error BD")

    try:
        session.execute("DELETE FROM paciente WHERE id_paciente = %s", [id_paciente])
        return {"mensaje": "Paciente eliminado correctamente"}
    except Exception as e:
        logging.error(f"Error eliminar paciente: {e}")
        raise HTTPException(status_code=500, detail=str(e))