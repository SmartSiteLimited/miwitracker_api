from pydantic import BaseModel, Field
from typing import Annotated, Any, Literal

class projects (BaseModel):
    id: int | None = None
    name: str | None = None

