from fastapi import APIRouter, Depends

from app.core.db import Database, get_dbo
from app.models.settings import Settings
from app.schema.response import ResponsePayload
from app.schema.settings import SettingPayload

router = APIRouter(prefix="/settings")


@router.post("/saveConfig")
async def save_config(payload: SettingPayload, dbo: Database = Depends(get_dbo)):
    settings = Settings(dbo)
    result = settings.save(payload.project, payload.attributes)

    return ResponsePayload(success=True, data=result)


@router.get("/{project}")
def get_config(project: str, dbo: Database = Depends(get_dbo)):
    settings = Settings(dbo)
    result = settings.get_by_project(project)
    return ResponsePayload(success=True, data=result)
