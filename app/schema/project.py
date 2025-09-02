from pydantic import BaseModel, Field


class Project(BaseModel):
    id: int
    name: str
    url: str