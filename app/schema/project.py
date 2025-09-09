from pydantic import BaseModel, Field


class Project(BaseModel):
    id: int | str | None = None
    name: str | None = None
    url: str | None = None
    miwi_group_id: int | str | None = None