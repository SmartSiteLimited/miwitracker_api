from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, Query
from pydantic import ValidationError

from app.core.db import Database, get_dbo
from app.core.miwi import Miwi
from app.models.devices import Devices
from app.schema import project
from app.schema.group import GroupCreatePayload
from app.schema.response import ResponsePayload

router = APIRouter(prefix="/groups")


@router.get("/")
@router.post("/")
async def get_group_list(dbo: Database = Depends(get_dbo)):
    miwi = Miwi(dbo)
    result = await miwi.get_group_list()
    return ResponsePayload(success=True, data=result)


@router.post("/create")
async def create_group(
    dbo: Database = Depends(get_dbo),
    payload: GroupCreatePayload = Body(...)
):
    if payload.group_name:
        miwi = Miwi(dbo)
        result = await miwi.create_group(payload.group_name, payload.description)
        return ResponsePayload(success=True, data=result)
    
    raise ValidationError("Group name is required.")
    

@router.delete("/{gid}")
async def delete_group(dbo: Database = Depends(get_dbo), gid=0):
    miwi = Miwi(dbo)
    result = await miwi.delete_group(gid)
    return ResponsePayload(success=True, data=result)
