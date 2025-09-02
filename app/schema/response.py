from typing import Generic, TypeVar

from pydantic import BaseModel

RT = TypeVar("RT")


class ResponsePayload(BaseModel, Generic[RT]):
    success: bool
    data: RT | None = None
    message: str | None = None
