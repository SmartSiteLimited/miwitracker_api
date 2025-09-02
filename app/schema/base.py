import json
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, model_validator
from pydantic.functional_serializers import PlainSerializer
from pydantic.functional_validators import BeforeValidator
from pydantic.main import IncEx


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


MySQLDateTime = Annotated[datetime, PlainSerializer(serialize_mysql_datetime), BeforeValidator(validate_mysql_datetime)]
JSONStrList = Annotated[list[str], BeforeValidator(lambda v: v.split(",") if isinstance(v, str) else v)]


class DbModel(BaseModel):
    def model_dump(
        self,
        *,
        mode: Literal["json", "python"] | str = "python",
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        context: Any | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal["none", "warn", "error"] = True,
        serialize_as_any: bool = False,
        db_fields: bool = False,
    ) -> dict[str, Any]:
        if db_fields:
            values = {}
            for key, field in self.model_computed_fields.items():
                if field.json_schema_extra and field.json_schema_extra.get("ignore_save", False):
                    continue
                if include is not None and key not in include:
                    continue
                if exclude is not None and key in exclude:
                    continue
                values[key] = self._model_dump_db(getattr(self, key))
            for key, field in self.model_fields.items():
                if field.json_schema_extra and field.json_schema_extra.get("ignore_save", False):
                    continue
                if include is not None and key not in include:
                    continue
                if exclude is not None and key in exclude:
                    continue
                values[key] = self._model_dump_db(getattr(self, key))
            return values

        return super().model_dump(
            mode=mode,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            serialize_as_any=serialize_as_any,
        )

    def model_dump_json(
        self,
        *,
        indent: int | None = None,
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        context: Any | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal["none", "warn", "error"] = True,
        serialize_as_any: bool = False,
        db_fields: bool = False,
    ) -> str:
        if db_fields:
            values = {}
            for key, field in self.model_computed_fields.items():
                if field.json_schema_extra and field.json_schema_extra.get("ignore_save", False):
                    continue

                values[key] = self._model_dump_db(getattr(self, key))

            for key, field in self.model_fields.items():
                if field.json_schema_extra and field.json_schema_extra.get("ignore_save", False):
                    continue

                values[key] = self._model_dump_db(getattr(self, key))

            return json.dumps(values, indent=indent, default=str)

        return super().model_dump_json(
            indent=indent,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            serialize_as_any=serialize_as_any,
        )

    def _model_dump_db(self, value):
        if isinstance(value, dict):
            return {k: self._model_dump_db(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._model_dump_db(item) for item in value]
        elif isinstance(value, DbModel):
            return value.model_dump(db_fields=True)
        elif isinstance(value, BaseModel):
            return value.model_dump()
        else:
            return value


class IdRecord(DbModel):
    id: int | None = None


class AliasRecord(DbModel):
    alias: str | None = None

    @model_validator(mode="after")
    def check_alias(self):
        if not self.alias:
            if hasattr(self, "title"):
                self.alias = self.title.lower().replace(" ", "-")
            elif hasattr(self, "name"):
                self.alias = self.name.lower().replace(" ", "-")
            else:
                self.alias = datetime.now().strftime("%Y-%m-%d %H-%M-%S")

        return self


class AuthorRecord(DbModel):
    created: MySQLDateTime | None = datetime.now()
    created_by: int | None = None
    created_by_name: str | None = None
    modified: MySQLDateTime | None = None
    modified_by: int | None = None
    modified_by_name: str | None = None

    @model_validator(mode="after")
    def init_created(self):
        if self.created:
            self.modified = datetime.now()
        else:
            self.created = datetime.now()

        if self.created_by is None:
            self.created_by = 0

        return self
