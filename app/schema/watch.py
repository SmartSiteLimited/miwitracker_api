from pydantic import BaseModel, Field
from typing import Annotated, Any, Literal
from datetime import datetime
from pydantic import BaseModel, model_validator
from pydantic.functional_serializers import PlainSerializer
from pydantic.functional_validators import BeforeValidator
from pydantic.main import IncEx
from app.schema.base import MySQLDateTime

def validate_mysql_datetime(v: Any):
    if v:
        if isinstance(v, datetime):
            return v

        if isinstance(v, str):
            return datetime.strptime(v, "%Y-%m-%d %H:%M:%S")

    return None


def serialize_mysql_datetime(v: Any):
    if v:
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%d %H:%M:%S")

        if isinstance(v, str):
            return v

    return None

class Watch(BaseModel):
    id: int | None = None
    IMEI_id : str | None = None
    project : str | None = None
    online_status : int | None = None
    created : MySQLDateTime | None = None
    updated : MySQLDateTime | None = None