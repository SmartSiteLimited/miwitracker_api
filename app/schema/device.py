from pydantic import BaseModel, Field, model_validator

from app.schema.base import MySQLDateTime


class Device(BaseModel):
    id: int
    project: str
    imei: str
    iccid: str | None = None
    firmware_version: str | None = None
    miwi_group_id: int | None = None
    phone_number: str | None = None
    created: MySQLDateTime
    updated: MySQLDateTime | None = None
