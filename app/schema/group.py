from pydantic import BaseModel, Field


class GroupCreatePayload(BaseModel):
    group_name: str = Field(min_length=1)
    description: str = Field(default="")
