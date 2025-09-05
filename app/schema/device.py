from pydantic import BaseModel, Field, model_validator

from app.schema.base import MySQLDateTime


class Device(BaseModel):
    id: int
    project: str
    imei: str
    firmware_version: str | None = None
    miwi_group_id: int | None = None
    iccid: str | None = None
    phone_number: str | None = None
    created: MySQLDateTime | None = None
    updated: MySQLDateTime | None = None
