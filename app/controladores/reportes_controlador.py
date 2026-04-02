from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Paciente, Cita, Pago, Abono
from app.servicios.auth_servicio import get_current_user
from datetime import datetime

router = APIRouter(
    prefix="/reportes",
    tags=["Reportes"],
    dependencies=[Depends(get_current_user)]
)

# ==========================================================
# DASHBOARD PRINCIPAL
# ==========================================================
@router.get("/dashboard")
def obtener_dashboard(db: Session = Depends(get_db)):

    try:
        # TOTAL PACIENTES
        total_pacientes = db.query(Paciente).count()

        # FECHA ACTUAL
        ahora = datetime.now()
        mes_actual = ahora.month
        anio_actual = ahora.year

        # INGRESOS DEL MES
        ingresos_mes = 0

        pagos = db.query(Pago).all()
        for pago in pagos:
            if pago.fecha_pago and pago.fecha_pago.month == mes_actual and pago.fecha_pago.year == anio_actual:
                ingresos_mes += pago.monto

        abonos = db.query(Abono).all()
        for abono in abonos:
            if abono.fecha_abono and abono.fecha_abono.month == mes_actual and abono.fecha_abono.year == anio_actual:
                ingresos_mes += abono.monto_abonado

        # CITAS DEL MES
        citas_mes = 0

        citas = db.query(Cita).all()
        for cita in citas:
            if cita.fecha_hora and cita.fecha_hora.month == mes_actual and cita.fecha_hora.year == anio_actual:
                citas_mes += 1

        return {
            "total_pacientes": total_pacientes,
            "ingresos_mes": ingresos_mes,
            "citas_mes": citas_mes
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================================
# RESUMEN (LO MISMO QUE DASHBOARD)
# ==========================================================
@router.get("/dashboard/resumen")
def obtener_resumen_dashboard(db: Session = Depends(get_db)):
    return obtener_dashboard(db)