from dataclasses import field
from typing import Any
from app.core import db 
from app.core.db import Query
from app.schema.settings import SettingFieldValue
from app.schema.base import DbModel
from pydantic import BaseModel
from typing import List
import json
from app.models.project import Projects
class Settings():
    def __init__(self):
        self.dbo = db.get_dbo()

    def get_setting_by_projects(self, project_name: str) -> str | None:
        result = None
        projectid = Projects().get_projectId_by_name(project_name)
        if not projectid  :
            return None
        query = Query()
        query.Select("field, value").From("setting_fields").Where("project_id = " + self.dbo.q(projectid))
        self.dbo.execute(query)
        result = self.dbo.fetch_all()
        if result:
            settings = {}
            for row in result:
                field = row['field']
                value = row['value']
                if isinstance(value, str | List) :
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        pass
                settings[field] = value
            return settings
        return None
        
    def update_form_value(self, field: str, value: Any , project_id) -> None:
        message = []
        if len(value) == 0 or not value:
            query = Query()
            query.Delete("setting_fields") \
                .Where("project_id = " + str(int(project_id))) \
                .Where("field = " + self.dbo.q(field))
            self.dbo.execute(str(query))
            self.dbo.commit()
            message.append(f"Settings for project '{project_id}' cleared successfully.")
            return message

        else:
            field_value = SettingFieldValue(field=field, value="", project_id=project_id)
            if isinstance(value, DbModel):
                field_value.value = value.model_dump_json(db_fields=True)
            elif isinstance(value, BaseModel):
                field_value.value = value.model_dump_json()
            elif isinstance(value, (list, dict, tuple)):
                field_value.value = json.dumps(value, default=str)
            else:
                field_value.value = str(value)
            #check if the field already exists
            query = Query()
            query.Select("project_id").From("setting_fields") \
                .Where("field = " + self.dbo.q(field))\
                .Where("project_id = " + self.dbo.q(project_id))
            self.dbo.execute(query)
            result = self.dbo.fetch_one()
            if result:
                self.dbo.update_object("setting_fields", field_value.model_dump(db_fields=True), ["field" , "project_id"], True)
            else:
                self.dbo.insert_object("setting_fields", field_value.model_dump(db_fields=True), True)
            message.append(f"Settings for project '{project_id}' updated successfully.")
            return message

    def set_settings_from_api(self , project:str , field: str, value: list[str] | None) -> None:
        message = []
        project_id = Projects().get_projectId_by_name(project)
        print(f"Project: {project}")
        if not project_id:
            raise ValueError(f"Project '{project}' not found")
        print(f"value" , value)
    
        self.update_form_value(field , value , project_id)

        return message
    
        
        
        