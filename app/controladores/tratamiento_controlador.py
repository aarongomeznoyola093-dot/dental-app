from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Tratamiento
from app.servicios.auth_servicio import get_current_user
import uuid

router = APIRouter(
    prefix="/tratamientos",
    tags=["Tratamientos"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/")
async def registrar_tratamiento(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    
    # Convertir duracion_estimada si es un diccionario
    duracion = data.get("duracion_estimada")
    if isinstance(duracion, dict):
        # Convertir diccionario a string, ej: {"meses": 48} -> "48 meses"
        if "meses" in duracion:
            duracion = f"{duracion['meses']} meses"
        else:
            duracion = str(duracion)
    
    nuevo_tratamiento = Tratamiento(
        id=str(uuid.uuid4()),
        nombre=data["nombre"],
        categoria=data.get("categoria"),
        descripcion=data.get("descripcion"),
        precio=data["precio"],
        duracion_estimada=duracion  # ✅ Ahora es string
    )
    
    db.add(nuevo_tratamiento)
    db.commit()
    db.refresh(nuevo_tratamiento)
    
    return {"mensaje": "Tratamiento registrado correctamente"}
# ==========================================================
# OBTENER TODOS LOS TRATAMIENTOS
# ==========================================================
@router.get("/")
def obtener_tratamientos(db: Session = Depends(get_db)):

    tratamientos = db.query(Tratamiento).all()

    resultado = []

    for t in tratamientos:
        resultado.append({
            "id_tratamiento": t.id,
            "nombre": t.nombre,
            "descripcion": t.descripcion,
            "precio": t.precio,
            "categoria": t.categoria,
            "duracion_estimada": t.duracion_estimada
        })

    return resultado


# ==========================================================
# OBTENER TRATAMIENTO POR ID
# ==========================================================
@router.get("/{id_tratamiento}")
def obtener_tratamiento(id_tratamiento: str, db: Session = Depends(get_db)):

    tratamiento = db.query(Tratamiento).filter(Tratamiento.id == id_tratamiento).first()

    if not tratamiento:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")

    return {
        "id_tratamiento": tratamiento.id,
        "nombre": tratamiento.nombre,
        "descripcion": tratamiento.descripcion,
        "precio": tratamiento.precio,
        "categoria": tratamiento.categoria,
        "duracion_estimada": tratamiento.duracion_estimada
    }


# ==========================================================
# ACTUALIZAR TRATAMIENTO
# ==========================================================
@router.put("/{id_tratamiento}")
async def actualizar_tratamiento(id_tratamiento: str, request: Request, db: Session = Depends(get_db)):

    data = await request.json()

    tratamiento = db.query(Tratamiento).filter(Tratamiento.id == id_tratamiento).first()

    if not tratamiento:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")

    tratamiento.nombre = data["nombre"]
    tratamiento.descripcion = data.get("descripcion")
    tratamiento.precio = data["precio"]
    tratamiento.categoria = data.get("categoria")
    tratamiento.duracion_estimada = data.get("duracion_estimada")

    db.commit()

    return {"mensaje": "Tratamiento actualizado correctamente"}


# ==========================================================
# ELIMINAR TRATAMIENTO
# ==========================================================
@router.delete("/{id_tratamiento}")
def eliminar_tratamiento(id_tratamiento: str, db: Session = Depends(get_db)):

    tratamiento = db.query(Tratamiento).filter(Tratamiento.id == id_tratamiento).first()

    if not tratamiento:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")

    db.delete(tratamiento)
    db.commit()

    return {"mensaje": "Tratamiento eliminado correctamente"}
# ==========================================================
# OBTENER TRATAMIENTO (RUTA COMPATIBLE CON FRONTEND)
# ==========================================================
@router.get("/tratamiento/{id_tratamiento}")
async def obtener_tratamiento_compatible(
    id_tratamiento: str, 
    db: Session = Depends(get_db)
):
    """Obtiene un tratamiento - ruta compatible con frontend"""
    tratamiento = db.query(Tratamiento).filter(Tratamiento.id == id_tratamiento).first()
    
    if not tratamiento:
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    
    return {
        "id_tratamiento": str(tratamiento.id),
        "nombre": tratamiento.nombre,
        "categoria": tratamiento.categoria,
        "descripcion": tratamiento.descripcion,
        "precio": float(tratamiento.precio) if tratamiento.precio else 0.0,
        "duracion_estimada": tratamiento.duracion_estimada
    }