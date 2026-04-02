from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Pago, Abono
from app.servicios.auth_servicio import get_current_user
import uuid
from datetime import datetime

router = APIRouter(
    prefix="/pagos",
    tags=["Pagos"],
    dependencies=[Depends(get_current_user)]
)

# ==========================================================
# REGISTRAR PAGO
# ==========================================================
@router.post("/pago")
async def registrar_pago(request: Request, db: Session = Depends(get_db)):

    data = await request.json()

    nuevo_pago = Pago(
        id=str(uuid.uuid4()),
        id_paciente=data["id_paciente"],
        id_cita=data["id_cita"],
        monto=data["monto"],
        fecha_pago=datetime.strptime(data["fecha_pago"], "%Y-%m-%d").date(),
        metodo_pago=data["metodo_pago"]
    )

    db.add(nuevo_pago)
    db.commit()
    db.refresh(nuevo_pago)

    return {"mensaje": "Pago registrado correctamente"}


# ==========================================================
# ACTUALIZAR PAGO
# ==========================================================
# ==========================================================
# ACTUALIZAR PAGO
# ==========================================================
@router.put("/pago")
async def actualizar_pago(request: Request, db: Session = Depends(get_db)):
    """Actualiza un pago existente (el ID viene en el cuerpo)"""
    try:
        data = await request.json()
        
        # Buscar el pago por ID (viene en el cuerpo)
        pago = db.query(Pago).filter(Pago.id == data["id_pago"]).first()
        
        if not pago:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
        
        # Actualizar campos
        pago.monto = data["monto"]
        pago.fecha_pago = datetime.strptime(data["fecha_pago"], "%Y-%m-%d").date()
        pago.metodo_pago = data["metodo_pago"]
        
        db.commit()
        
        return {"mensaje": "Pago actualizado correctamente"}
        
    except Exception as e:
        print(f"Error al actualizar pago: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================================
# REGISTRAR ABONO
# ==========================================================
@router.post("/abono")
async def registrar_abono(request: Request, db: Session = Depends(get_db)):

    data = await request.json()

    nuevo_abono = Abono(
        id=str(uuid.uuid4()),
        id_paciente=data["id_paciente"],
        id_tratamiento=data.get("id_tratamiento"),
        fecha_abono=datetime.strptime(data["fecha_abono"], "%Y-%m-%d").date(),
        monto_abonado=data["monto_abonado"],
        saldo_restante=data["saldo_restante"],
        estado=data["estado"]
    )

    db.add(nuevo_abono)
    db.commit()
    db.refresh(nuevo_abono)

    return {"mensaje": "Abono registrado correctamente"}
# ==========================================================
# ELIMINAR PAGO
# ==========================================================
@router.delete("/pago")
async def eliminar_pago(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        
        pago = db.query(Pago).filter(Pago.id == data["id_pago"]).first()
        
        if not pago:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
        
        db.delete(pago)
        db.commit()
        
        return {"mensaje": "Pago eliminado correctamente"}
        
    except Exception as e:
        print(f"Error al eliminar pago: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    # ==========================================================
# ELIMINAR ABONO
# ==========================================================
@router.delete("/abono")
async def eliminar_abono(request: Request, db: Session = Depends(get_db)):
    """Elimina un abono existente"""
    try:
        data = await request.json()
        
        # Buscar el abono por ID
        abono = db.query(Abono).filter(Abono.id == data["id_abono"]).first()
        
        if not abono:
            raise HTTPException(status_code=404, detail="Abono no encontrado")
        
        db.delete(abono)
        db.commit()
        
        return {"mensaje": "Abono eliminado correctamente"}
        
    except Exception as e:
        print(f"Error al eliminar abono: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))