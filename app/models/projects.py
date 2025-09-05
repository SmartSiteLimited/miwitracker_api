from app.schema.project import Project
from app.core import db
from app.core.db import Database, Query


class Projects:
    def __init__(self, dbo: Database):
        self.dbo = dbo

    def get_project_id(self, project_name: str) -> int | None:
        query = Query()
        query.Select("id").From("projects").Where("name = " + self.dbo.q(project_name))
        self.dbo.execute(query)
        return self.dbo.fetch_result()

    def get_projects(self) -> list[Project]:
        query = Query()
        query.Select("*").From("projects")
        self.dbo.execute(query)
        results = self.dbo.fetch_all()

        return [Project(**row) for row in results] if results else []

    def check_group_id_exists_by_project(self, project_name: str) -> int | None:
        query = Query()
        query.Select("miwi_group_id").From("projects").Where("name = " + self.dbo.q(project_name))
        self.dbo.execute(query)
        result = self.dbo.fetch_one()
        return result["miwi_group_id"] if result else None