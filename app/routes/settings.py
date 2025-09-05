from typing import Any, Dict, List, Optional

import json

from fastapi import APIRouter, Body, Depends, Form, Query ,Form
from pydantic import BaseModel, field_validator

from app.core.db import Database, get_dbo
from app.core.logger import get_logger
# from app.core.miwi import Miwi
from app.models.settings import Settings
from app.schema.response import ResponsePayload

router = APIRouter(prefix="/settings")

class SaveConfigPayload(BaseModel):
    attributes: List[Any]
    project: str

    @field_validator('attributes', mode='before')
    def parse_attributes(cls, v):
        # Accept a JSON parse object type and parse it
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                raise ValueError('attributes must be a valid JSON array of objects')
        return v

@router.post("/saveConfig")
async def saveConfig(dbo: Database = Depends(get_dbo), payload: SaveConfigPayload = Body(...)):

    settings = Settings(dbo)
    result = settings.saveConfig(payload.attributes, payload.project)

    return ResponsePayload(success=True, data=result)
@router.get("/{project}")
def getConfig(project: str, dbo: Database = Depends(get_dbo)):
    settings = Settings(dbo)
    result = settings.get_setting_by_projects(project)
    return ResponsePayload(success=True, data=result)

