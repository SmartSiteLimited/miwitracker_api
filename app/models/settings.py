from typing import Any, List
import json
from app.core.db import Database, Query
from app.schema.settings import SettingFieldValue
from app.schema.base import DbModel
from pydantic import BaseModel
from app.models.projects import Projects

class Settings:
    def __init__(self, dbo: Database):
        self.dbo = dbo

    def get_setting_by_projects(self, project_name: str) -> dict | None:
        query = Query()
        query.Select("field, value").From("project_settings").Where("project_name = " + self.dbo.q(project_name))
        self.dbo.execute(query)
        result = self.dbo.fetch_all()
        if result:
            settings = {}
            for row in result:
                field = row["field"]
                value = row["value"]
                print(f"Raw DB value for {field}: {value!r}")  # Debug: Log raw value
                if isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        pass  # Keep as string if not JSON
                settings[field] = value
                print(f"Parsed value for {field}: {value!r}")  # Debug: Log parsed value
            return settings
        return None

    def update_form_value(self, field: str, value: Any, project_name: str) -> list[str]:
        message = []
        if not value or (isinstance(value, (list, dict, tuple)) and len(value) == 0):
            query = Query()
            query.Delete("project_settings").Where("project_name = " + self.dbo.q(project_name)).Where(
                "field = " + self.dbo.q(field)
            )
            self.dbo.execute(str(query))
            self.dbo.commit()
            message.append(f"Settings for project '{project_name}' cleared successfully.")
            return message

        field_value = SettingFieldValue(field=field, value="", project_name=project_name)
        if isinstance(value, DbModel):
            field_value.value = value.model_dump_json(db_fields=True)
        elif isinstance(value, BaseModel):
            field_value.value = value.model_dump_json()
        elif isinstance(value, (list, dict, tuple)):
            # Use separators=(',', ':') for compact JSON without extra spaces
            field_value.value = json.dumps(value, default=str, separators=(',', ':'))
        else:
            field_value.value = str(value)
        
        print(f"Storing value for {field}: {field_value.value!r}")  # Debug: Log stored value

        # Check if the field already exists
        query = Query()
        query.Select("project_name").From("project_settings").Where("field = " + self.dbo.q(field)).Where(
            "project_name = " + self.dbo.q(project_name)
        )
        self.dbo.execute(query)
        result = self.dbo.fetch_one()
        if result:
            self.dbo.update_object(
                "project_settings", field_value.model_dump(db_fields=True), ["field", "project_name"], True
            )
        else:
            self.dbo.insert_object("project_settings", field_value.model_dump(db_fields=True), True)
        message.append(f"Settings for project '{project_name}' updated successfully.")
        return message

    def set_settings_from_api(self, field: str, value: list[str] | None, project_name: str) -> list[str]:
        print(f"Project: {project_name}")
        if not project_name:
            raise ValueError(f"Project '{project_name}' not found")
        print(f"Value for {field}: {value!r}")  # Debug: Log value before storage
        return self.update_form_value(field, value, project_name)

    def saveConfig(self, attributes, project_name: str):
        message = []
        print(f"Project: {project_name}")
        if not attributes:
            return message

        if isinstance(attributes, str):
            try:
                attributes = json.loads(attributes)
            except json.JSONDecodeError:
                return message

        items = []
        if isinstance(attributes, dict):
            if "key" in attributes and "value" in attributes:
                items.append(attributes)
            else:
                for k, v in attributes.items():
                    items.append({"key": k, "value": v})
        elif isinstance(attributes, list):
            for it in attributes:
                if isinstance(it, dict) and "key" in it and "value" in it:
                    items.append(it)
        else:
            return message

        for it in items:
            field = it.get("key")
            raw_value = it.get("value")
            if not field:
                continue

            if isinstance(raw_value, str):
                if raw_value.strip() == "":
                    value_for_api = []
                elif "," in raw_value:
                    # Split and clean: remove spaces and filter empty strings
                    value_for_api = [s.strip() for s in raw_value.split(",") if s.strip()]
                else:
                    value_for_api = [raw_value.strip()]
            else:
                value_for_api = raw_value

            print(f"Processed value for {field}: {value_for_api!r}")  # Debug: Log processed value
            try:
                result = self.set_settings_from_api(field, value_for_api, project_name)
                if result:
                    message.extend(result)
            except Exception as e:
                message.append(f"Failed to save '{field}': {e}")
        return message