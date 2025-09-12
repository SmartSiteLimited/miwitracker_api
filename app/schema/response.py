from pydantic import BaseModel


class ResponsePayload[RT](BaseModel):
    success: bool
    data: RT | None = None
    message: str | None = None
