from fastapi import APIRouter
from fastapi.params import Body, Depends

from app.core.db import Database, get_dbo
from app.models.projects import Projects
from app.schema.project import Project
from app.schema.response import ResponsePayload

router = APIRouter(prefix="/projects")


@router.get("/")
async def get_projects(dbo: Database = Depends(get_dbo)):
    projects = Projects(dbo)
    data = projects.get_projects()

    return ResponsePayload(success=True, data=data)


@router.post("/saveProjects")
async def save_projects(payload: dict[str, list[Project]] = Body(...), dbo: Database = Depends(get_dbo)):
    projects_model = Projects(dbo)
    result = projects_model.save_projects(payload["projects"])
    return ResponsePayload(success=True, data=result)


@router.delete("/{project_name}")
async def delete_project(project_name: str = "", dbo: Database = Depends(get_dbo)):
    projects_model = Projects(dbo)
    isdeleted = projects_model.delete_project(str(project_name))
    message = "Project deleted successfully." if isdeleted else "Project not found."
    return ResponsePayload(success=True, data=message)
