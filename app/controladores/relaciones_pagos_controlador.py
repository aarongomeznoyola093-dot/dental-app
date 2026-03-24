from fastapi import APIRouter
router = APIRouter(prefix="/pagos", tags=["Pagos"])
@router.get("/")
async def obtener_pagos():
    return {"mensaje": "Pagos funcionando"}
