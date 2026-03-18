
from fastapi import APIRouter, Depends, Request, HTTPException, Query
import uuid
from datetime import date
import logging
from datetime import date, datetime, timedelta
from cassandra.util import Date as CassandraDate  
from app.db_session import get_session
from app.servicios.auth_servicio import get_current_user 

router = APIRouter(
    tags=["Citas"],  
    dependencies=[Depends(get_current_user)]  
)


session = get_session()




@router.post("/cita")
async def registrar_cita(data: Request, force: bool = Query(False)):
    try:
        body = await data.json()

      
        
        try:
            fecha_hora_obj = datetime.fromisoformat(body["fecha_hora"])
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Formato de fecha y hora inválido.")

        # --- 3. INICIO DE LA VERIFICACIÓN ---
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
            fecha_hora_obj, 
            body["motivo"], body["estado"]
        ))
        return {"mensaje": "Cita guardada correctamente"}

    except HTTPException as http_exc:
        raise http_exc 
    except Exception as e:
        logging.error(f" Error al procesar la cita: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.put("/cita/{id_cita}") 
async def actualizar_cita(id_cita: uuid.UUID, data: Request):
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
        logging.error(f" Error al actualizar la cita {id_cita}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.delete("/cita/{id_cita}") 
async def eliminar_cita(id_cita: uuid.UUID, data: Request):
    try:
        body = await data.json()
        id_paciente_uuid = uuid.UUID(body["id_paciente"])

        logging.info(f"Iniciando eliminación de cita {id_cita} para paciente {id_paciente_uuid}")

        session.execute("DELETE FROM cita_tratamiento WHERE id_paciente = %s AND id_cita = %s", [id_paciente_uuid, id_cita])
        session.execute("DELETE FROM pago WHERE id_paciente = %s AND id_cita = %s", [id_paciente_uuid, id_cita])
        session.execute("DELETE FROM cita WHERE id_paciente = %s AND id_cita = %s", [id_paciente_uuid, id_cita])

        return {"mensaje": "Cita eliminada correctamente"}
    except Exception as e:
        logging.error(f" Error al eliminar la cita {id_cita}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")
    

    
@router.get("/citas/calendario")
async def obtener_citas_calendario():

    
    def format_row_simple(row):
        if not row: return {}
        row_dict = dict(row)
        for key, value in row_dict.items():
            if isinstance(value, uuid.UUID):
                row_dict[key] = str(value)

          
            elif isinstance(value, datetime): 
                row_dict[key] = value 
            
            elif isinstance(value, CassandraDate):
                row_dict[key] = value.date() 
            
        return row_dict
    
    

    try:
        # 1. Obtener todos los pacientes 
        pacientes_rows = session.execute("SELECT id_paciente, nombre, apellido_pat FROM paciente")
        pacientes_map = {
            str(p['id_paciente']): f"{p['nombre']} {p['apellido_pat']}"
            for p in pacientes_rows
        }

        # 2. Obtener todas las citas
        citas_rows = session.execute("SELECT id_paciente, id_cita, fecha_hora, motivo, estado FROM cita")

        eventos = []
        for cita_row in citas_rows:
            
            if cita_row['estado'] != 'programada':
                continue

            
            cita = format_row_simple(cita_row)

            
            paciente_nombre = pacientes_map.get(cita['id_paciente'], "Paciente Desconocido")
            titulo_evento = f"{paciente_nombre} ({cita['motivo']})"

            
            start_time = cita.get('fecha_hora')
            if not isinstance(start_time, datetime):
                logging.warning(f"Cita {cita.get('id_cita')} omitida: fecha_hora inválida.")
                continue

            end_time = start_time + timedelta(hours=1) 

            eventos.append({
                "id": cita['id_cita'],
                "title": titulo_evento,
                "start": start_time.isoformat(), 
                "end": end_time.isoformat()
            })

        return eventos
    except Exception as e:
        logging.error(f" Error al obtener citas para calendario: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")