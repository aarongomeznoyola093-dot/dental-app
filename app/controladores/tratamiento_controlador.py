from fastapi import APIRouter, Depends, HTTPException, Request
from app.db_session import get_db_session
from app.servicios.auth_servicio import get_current_user
import uuid
import logging
from decimal import Decimal

router = APIRouter(prefix="/tratamientos", tags=["Tratamientos"], dependencies=[Depends(get_current_user)])

@router.post("/tratamiento")
async def registrar_tratamiento(data: Request):
    session = get_db_session()
    if session is None:
        raise HTTPException(status_code=500, detail="Error de conexión BD")
    
    try:
        body = await data.json()
        query = """
        INSERT INTO tratamiento (id_tratamiento, nombre, categoria, descripcion, precio, duracion_estimada)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        session.execute(query, (
            uuid.UUID(body["id_tratamiento"]), 
            body["nombre"], 
            body["categoria"],
            body["descripcion"], 
            Decimal(str(body["precio"])), 
            body["duracion_estimada"]
        ))
        return {"mensaje": "Tratamiento guardado correctamente"}
    except Exception as e:
        logging.error(f"Error al procesar el tratamiento: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/")
async def obtener_tratamientos():
    session = get_db_session()
    if session is None:
        raise HTTPException(status_code=500, detail="Error de conexión BD")
    
    try:
        rows = session.execute("SELECT * FROM tratamiento")
        tratamientos = []
        for row in rows:
            precio_valor = 0.0
            if hasattr(row, 'precio') and row.precio is not None:
                precio_valor = float(row.precio)
            elif hasattr(row, 'costo') and row.costo is not None:
                precio_valor = float(row.costo)
            
            tratamiento = {
                "id_tratamiento": str(row['id_tratamiento']),
                "nombre": row['nombre'],
                "descripcion": row.get('descripcion', ''),
                "costo": precio_valor,
                "precio": precio_valor,
                "categoria": row.get('categoria', ''),
                "duracion_estimada": row.get('duracion_estimada', '')
            }
            tratamientos.append(tratamiento)
        return tratamientos
    except Exception as e:
        logging.error(f"Error al cargar tratamientos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tratamiento/{id_tratamiento}")
async def actualizar_tratamiento(id_tratamiento: uuid.UUID, data: Request):
    session = get_db_session()
    if session is None:
        raise HTTPException(status_code=500, detail="Error de conexión BD")
    
    try:
        body = await data.json()
        query = """
        UPDATE tratamiento SET nombre = %s, categoria = %s, descripcion = %s, precio = %s, duracion_estimada = %s
        WHERE id_tratamiento = %s
        """
        session.execute(query, (
            body["nombre"], 
            body["categoria"], 
            body["descripcion"],
            Decimal(str(body["precio"])), 
            body["duracion_estimada"], 
            id_tratamiento
        ))
        return {"mensaje": "Tratamiento actualizado correctamente"}
    except Exception as e:
        logging.error(f"Error al actualizar el tratamiento {id_tratamiento}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.delete("/tratamiento/{id_tratamiento}")
async def eliminar_tratamiento(id_tratamiento: uuid.UUID):
    session = get_db_session()
    if session is None:
        raise HTTPException(status_code=500, detail="Error de conexión BD")
    
    try:
        session.execute("DELETE FROM tratamiento WHERE id_tratamiento = %s", [id_tratamiento])
        return {"mensaje": "Tratamiento eliminado correctamente"}
    except Exception as e:
        logging.error(f"Error al eliminar el tratamiento {id_tratamiento}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/tratamiento/{id_tratamiento}")
async def obtener_tratamiento(id_tratamiento: uuid.UUID):
    session = get_db_session()
    if session is None:
        raise HTTPException(status_code=500, detail="Error de conexión BD")
    
    try:
        query = "SELECT * FROM tratamiento WHERE id_tratamiento = %s"
        row = session.execute(query, [id_tratamiento]).one()
        
        if not row:
            raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
        
        tratamiento = {
            "id_tratamiento": str(row['id_tratamiento']),
            "nombre": row['nombre'],
            "descripcion": row.get('descripcion', ''),
            "precio": float(row['precio']) if row['precio'] else 0.0,
            "categoria": row.get('categoria', ''),
            "duracion_estimada": row.get('duracion_estimada', '')
        }
        return tratamiento
        
    except Exception as e:
        logging.error(f"Error al obtener tratamiento {id_tratamiento}: {e}")
        raise HTTPException(status_code=500, detail=str(e))