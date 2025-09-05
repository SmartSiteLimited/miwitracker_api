from pydantic import BaseModel, ConfigDict
import json
from app.schema.base import IdRecord, DbModel


class SettingFieldValue(DbModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    project_name: str | None = None
    field: str
    value: str | None = None


class SettingFieldValues(DbModel):
    @classmethod
    def parse_form_values(cls, form_values: list[SettingFieldValue]):
        # to dict
        form_values_dict = {}
        for form_value in form_values:
            # is json?
            if isinstance(form_value.value, str):
                try:
                    form_value.value = json.loads(form_value.value)
                except json.JSONDecodeError:
                    pass

            form_values_dict[form_value.field] = form_value.value

        return form_values_dict
