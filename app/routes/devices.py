from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, Query

from app.core.db import Database, get_dbo
from app.core.logger import get_logger
from app.core.miwi import Miwi
from app.models.devices import Devices
from app.schema.response import ResponsePayload

router = APIRouter(prefix="/devices")


@router.post("/task/check-online")
async def check_online(dbo: Database = Depends(get_dbo), body: Dict[str, Any] = Body(...)):
    imeis = body.get("imeis")
    if imeis is None or len(imeis) == 0:
        return ResponsePayload(success=False, message="No imeis provided")

    miwi = Miwi(dbo)
    result = await miwi.check_onlines(imeis.split(","))

    return ResponsePayload(success=True, data=result)


@router.post("/task/locate/{imei}")
async def locate(dbo: Database = Depends(get_dbo), imei=""):
    miwi = Miwi(dbo)
    result = await miwi.locate(imei)

    return ResponsePayload(success=True, data=result)


@router.get("/{project}")
@router.post("/{project}")
@router.post("/")
async def get_devices(
    dbo: Database = Depends(get_dbo), project="", body: Optional[Dict[str, Any]] = Body(default=None)
):
    devices = Devices(dbo)

    filters = body.get("filters") if body else None
    data = devices.get_devices(project, filters or {})

    return ResponsePayload(success=True, data=data)
