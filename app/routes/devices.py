from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, Query

from app.core import miwi
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

@router.post("/task/setphonebook/{imei}")
async def set_book_phone(dbo: Database = Depends(get_dbo) ,imei=""):
    miwi = Miwi(dbo)
    result = await miwi.setPhoneBook(imei)

    return ResponsePayload(success=True, data=result)

@router.post("/task/setblockphone/{imei}")
async def setblockphone(dbo: Database = Depends(get_dbo) ,imei=""):
    miwi = Miwi(dbo)
    result = await miwi.setBlockPhone(imei)

    return ResponsePayload(success=True, data=result)

@router.post("/task/setsos/{imei}")
async def setsos(dbo: Database = Depends(get_dbo) ,imei=""):
    miwi = Miwi(dbo)
    result = await miwi.setSOS(imei)

    return ResponsePayload(success=True, data=result)

@router.post("/task/sethealth/{imei}")
async def sethealth(dbo: Database = Depends(get_dbo) ,imei=""):
    miwi = Miwi(dbo)
    result = await miwi.setHealth(imei)

    return ResponsePayload(success=True, data=result)

@router.post("/task/setcallcenter/{imei}")
async def setcallcenter(dbo: Database = Depends(get_dbo) ,imei=""):
    miwi = Miwi(dbo)
    result = await miwi.setCallCenter(imei)

    return ResponsePayload(success=True, data=result)

@router.post("/task/reboot/{imei}")
async def setReboot(dbo: Database = Depends(get_dbo) ,imei=""):
    miwi = Miwi(dbo)
    result = await miwi.setReboot(imei)

    return ResponsePayload(success=True, data=result)

@router.post("/task/poweroff/{imei}")
async def setPowerOff(dbo: Database = Depends(get_dbo) ,imei=""):
    miwi = Miwi(dbo)
    result = await miwi.setPowerOff(imei)

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

@router.post("/save/{project}")
async def save_device(dbo: Database = Depends(get_dbo), project="", payload: Dict[str, Any] = Body(...)):
    device = Devices(dbo)
    result = await device.save_device(payload , project)
    return ResponsePayload(success=True, data=result)

@router.get("/updateICCID/get_devices")
async def update_iccid(dbo: Database = Depends(get_dbo), miwi_group_id=None):
    miwi = Miwi(dbo)
    result = await miwi.update_iccid(miwi_group_id)
    return ResponsePayload(success=True, data=result)

@router.get("/groupsList/options")
async def get_groups_list(dbo: Database = Depends(get_dbo)):
    miwi = Miwi(dbo)
    result = await miwi.get_groups_list()
    return ResponsePayload(success=True, data=result)

@router.get("/addMiwiGroup/{project}")
async def add_miwi_group(dbo: Database = Depends(get_dbo), project=""):
    miwi = Miwi(dbo)
    result = await miwi.add_miwi_group(project)
    return ResponsePayload(success=True, data=result)

@router.get("/addupdateGroupId/{project}")
async def add_update_group_id(dbo: Database = Depends(get_dbo), project = "" ):
    miwi = Miwi(dbo)
    result = await miwi.add_update_group_and_icc(project)
    return ResponsePayload(success=True, data=result)

@router.get("/groupList/list")
async def get_group_list(dbo: Database = Depends(get_dbo)):
    miwi = Miwi(dbo)
    result = await miwi.get_group_list()
    return ResponsePayload(success=True, data=result)

@router.delete("/deletegroups/{id}")
async def delete_groups(dbo: Database = Depends(get_dbo), id = '' ):
    miwi = Miwi(dbo)
    result = await miwi.delete_group(id)
    return ResponsePayload(success=True, data=result)