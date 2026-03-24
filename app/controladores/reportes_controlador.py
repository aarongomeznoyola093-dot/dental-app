from fastapi import APIRouter, Depends, HTTPException
from app.db_session import get_db_session
from app.servicios.auth_servicio import get_current_user
from datetime import datetime

router = APIRouter(prefix="/reportes", tags=["Reportes"], dependencies=[Depends(get_current_user)])

def convertir_fecha(fecha_obj):
    if not fecha_obj:
        return None
    if isinstance(fecha_obj, datetime):
        return fecha_obj
    try:
        return datetime.strptime(str(fecha_obj), '%Y-%m-%d')
    except:
        return None

@router.get("/dashboard")
async def obtener_datos_dashboard():
    session = get_db_session()
    if session is None:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    
    try:
        rows = session.execute("SELECT id_paciente FROM paciente")
        total_pacientes = len(list(rows))
        
        ahora = datetime.utcnow()
        mes_actual = ahora.month
        anio_actual = ahora.year
        
        ingresos = 0.0
        citas_mes = 0
        
        pagos = session.execute("SELECT monto, fecha_pago FROM pago ALLOW FILTERING")
        for p in pagos:
            fecha = convertir_fecha(p['fecha_pago'])
            if fecha and fecha.month == mes_actual and fecha.year == anio_actual:
                ingresos += float(p['monto'])
        
        abonos = session.execute("SELECT monto_abonado, fecha_abono FROM abono ALLOW FILTERING")
        for a in abonos:
            fecha = convertir_fecha(a['fecha_abono'])
            if fecha and fecha.month == mes_actual and fecha.year == anio_actual:
                ingresos += float(a['monto_abonado'])
        
        citas = session.execute("SELECT fecha_hora FROM cita ALLOW FILTERING")
        for c in citas:
            fecha = convertir_fecha(c['fecha_hora'])
            if fecha and fecha.month == mes_actual and fecha.year == anio_actual:
                citas_mes += 1
        
        return {
            "total_pacientes": total_pacientes,
            "ingresos_mes": ingresos,
            "citas_mes": citas_mes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/resumen")
async def obtener_resumen_dashboard():
    return await obtener_datos_dashboard()
