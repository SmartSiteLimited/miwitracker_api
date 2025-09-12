from app.core.db import Database, Query
from app.schema.settings import ProjectSetting, SettingAttributePayload


class Settings:
    def __init__(self, dbo: Database):
        self.dbo = dbo

    def get_by_project(self, project_name: str) -> dict | None:
        query = Query()
        query.Select("*").From("project_settings").Where("project_name = " + self.dbo.q(project_name))
        self.dbo.execute(query)
        result = self.dbo.fetch_all()

        if result:
            settings = [ProjectSetting(**setting) for setting in result]
            return {setting.field: setting.value for setting in settings}

        return None

    def update_form_value(self, project_name: str, field: str, value: str | None = None) -> list[str]:
        if value is None or (isinstance(value, str) and value.strip() == ""):
            query = Query()
            query.Delete("project_settings").Where("project_name = " + self.dbo.q(project_name)).Where(
                "field = " + self.dbo.q(field)
            )
            self.dbo.execute(str(query))
            self.dbo.commit()
            return True

        else:
            record = ProjectSetting(field=field, value=value, project_name=project_name)
            self.dbo.insert_object("project_settings", record.model_dump(db_fields=True), True)

        return True

    def save(self, project_name: str, attributes: list[SettingAttributePayload]) -> list[str]:
        existing_settings = self.get_by_project(project_name)
        existing_settings = existing_settings.keys() if existing_settings else []

        saved_fields = []

        for attr in attributes:
            self.update_form_value(project_name, attr.key, attr.value)
            saved_fields.append(attr.key)

        # Remove settings that are not in the new attributes
        for field in existing_settings:
            if field not in saved_fields:
                self.update_form_value(project_name, field, None)

        return True
