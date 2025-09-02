from fastapi import APIRouter, Query
from fastapi.params import Body, Depends

from app.core.db import Database, get_dbo
from app.models.projects import Projects
from app.schema.response import ResponsePayload

router = APIRouter(prefix="/projects")


@router.get("/")
async def get_projects(dbo: Database=Depends(get_dbo)):
    projects = Projects(dbo)
    data = projects.get_projects()

    return ResponsePayload(success=True, data=data)
