from pydantic import BaseModel


class Project(BaseModel):
    id: int | str | None = None
    name: str | None = None
    url: str | None = None
    miwi_group_id: int | str | None = None
