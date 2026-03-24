from fastapi import APIRouter, Depends, HTTPException, Request, Query
from app.db_session import get_db_session
from app.servicios.auth_servicio import get_current_user
import uuid
import logging
from datetime import datetime, timedelta

router = APIRouter(prefix="/citas", tags=["Citas"], dependencies=[Depends(get_current_user)])

@router.post("/")
async def registrar_cita(data: Request, force: bool = Query(False)):
    session = get_db_session()
    try:
        body = await data.json()
        try:
            fecha_hora_obj = datetime.fromisoformat(body["fecha_hora"])
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Formato de fecha y hora inválido.")
        
        if not force:
            query_check = "SELECT id_cita FROM cita WHERE fecha_hora = %s ALLOW FILTERING"
            cita_existente = session.execute(query_check, [fecha_hora_obj]).one()
            if cita_existente:
                raise HTTPException(
                    status_code=409, 
                    detail="¡Conflicto! Ya existe una cita en ese horario. ¿Desea registrarla de todos modos?"
                )
        
        query_insert = """
        INSERT INTO cita (id_cita, id_paciente, fecha_hora, motivo, estado)
        VALUES (%s, %s, %s, %s, %s)
        """
        session.execute(query_insert, (
            uuid.UUID(body["id_cita"]), uuid.UUID(body["id_paciente"]),
            fecha_hora_obj, body["motivo"], body["estado"]
        ))
        return {"mensaje": "Cita guardada correctamente"}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logging.error(f"Error al procesar la cita: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")
    
@router.get("/calendario")
async def obtener_citas_calendario():
    print("=" * 50)
    print("ENDPOINT CALENDARIO LLAMADO")
    print("=" * 50)
    
    try:
        session = get_db_session()
        print(f"1. Sesión obtenida: {session is not None}")
        
        if session is None:
            print("❌ Error: No se pudo conectar a la base de datos")
            raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
        
        print("2. Obteniendo pacientes...")
        pacientes_rows = list(session.execute("SELECT id_paciente, nombre, apellido_pat FROM paciente"))
        print(f"   Pacientes encontrados: {len(pacientes_rows)}")
        
        pacientes_map = {
            str(p['id_paciente']): f"{p['nombre']} {p['apellido_pat']}"
            for p in pacientes_rows
        }
        
        print("3. Obteniendo citas...")
        citas_rows = list(session.execute("SELECT id_paciente, id_cita, fecha_hora, motivo, estado FROM cita"))
        print(f"   Citas encontradas: {len(citas_rows)}")
        
        eventos = []
        from datetime import datetime, timedelta
        
        for cita_row in citas_rows:
            if cita_row['estado'] != 'programada':
                continue
            
            paciente_nombre = pacientes_map.get(str(cita_row['id_paciente']), "Paciente Desconocido")
            titulo_evento = f"{paciente_nombre} ({cita_row['motivo']})"
            
            start_time = cita_row['fecha_hora']
            if isinstance(start_time, datetime):
                end_time = start_time + timedelta(hours=1)
                eventos.append({
                    "id": str(cita_row['id_cita']),
                    "title": titulo_evento,
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                })
        
        print(f"4. Eventos generados: {len(eventos)}")
        print("=" * 50)
        return eventos
        
    except Exception as e:
        print(f"❌ ERROR en calendario: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    
@router.get("/{id_cita}")
async def obtener_cita(id_cita: uuid.UUID):
    session = get_db_session()
    if session is None:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    
    try:
        # Buscar la cita por ID
        query = "SELECT * FROM cita WHERE id_cita = %s ALLOW FILTERING"
        row = session.execute(query, [id_cita]).one()
        
        if not row:
            raise HTTPException(status_code=404, detail="Cita no encontrada")
        
        cita = {
            "id_cita": str(row['id_cita']),
            "id_paciente": str(row['id_paciente']),
            "fecha_hora": str(row['fecha_hora']),
            "motivo": row['motivo'],
            "estado": row['estado']
        }
        return cita
        
    except Exception as e:
        logging.error(f"Error al obtener cita {id_cita}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{id_cita}")
async def actualizar_cita(id_cita: uuid.UUID, data: Request):
    session = get_db_session()
    try:
        body = await data.json()
        id_paciente_uuid = uuid.UUID(body["id_paciente"])
        query = """
        UPDATE cita SET fecha_hora = %s, motivo = %s, estado = %s
        WHERE id_paciente = %s AND id_cita = %s
        """
        session.execute(query, (
            body["fecha_hora"], body["motivo"], body["estado"],
            id_paciente_uuid, id_cita
        ))
        return {"mensaje": "Cita actualizada correctamente"}
    except Exception as e:
        logging.error(f"Error al actualizar la cita {id_cita}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")
    
    

@router.delete("/{id_cita}")
async def eliminar_cita(id_cita: uuid.UUID, data: Request):
    session = get_db_session()
    try:
        body = await data.json()
        id_paciente_uuid = uuid.UUID(body["id_paciente"])
        
        session.execute("DELETE FROM cita_tratamiento WHERE id_paciente = %s AND id_cita = %s", [id_paciente_uuid, id_cita])
        session.execute("DELETE FROM pago WHERE id_paciente = %s AND id_cita = %s", [id_paciente_uuid, id_cita])
        session.execute("DELETE FROM cita WHERE id_paciente = %s AND id_cita = %s", [id_paciente_uuid, id_cita])
        
        return {"mensaje": "Cita eliminada correctamente"}
    except Exception as e:
        logging.error(f"Error al eliminar la cita {id_cita}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


    
@router.post("/cita-tratamiento")
async def registrar_cita_tratamiento(data: Request):
    session = get_db_session()
    if session is None:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    
    try:
        body = await data.json()
        
        # Validar campos requeridos
        id_paciente = uuid.UUID(body["id_paciente"])
        id_cita = uuid.UUID(body["id_cita"])
        id_tratamiento = uuid.UUID(body["id_tratamiento"])
        observaciones = body.get("observaciones", "")
        resultado = body.get("resultado", "")
        
        # Insertar en la tabla cita_tratamiento
        query = """
        INSERT INTO cita_tratamiento (id_paciente, id_cita, id_tratamiento, observaciones, resultado)
        VALUES (%s, %s, %s, %s, %s)
        """
        session.execute(query, (
            id_paciente, id_cita, id_tratamiento, observaciones, resultado
        ))
        
        return {"mensaje": "Tratamiento asignado a la cita correctamente"}
        
    except Exception as e:
        logging.error(f"Error al procesar cita-tratamiento: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")
    
    