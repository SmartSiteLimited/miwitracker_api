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

    def get_project_group_id(self, project_name: str) -> int | None:
        query = Query()
        query.Select("miwi_group_id").From("projects").Where("name = " + self.dbo.q(project_name))
        self.dbo.execute(query)
        result = self.dbo.fetch_one()
        return result["miwi_group_id"] if result else None

    def save_projects(self, projects: list[Project]):
        if not projects:
            raise ValueError("No projects to save.")

        for project in projects:
            if project.id and project.id > 0:
                update_data = {
                    "id": project.id,
                    "name": project.name,
                    "url": project.url,
                    "miwi_group_id": project.miwi_group_id,
                }
                self.dbo.update_object("projects", update_data, "id")
            else:
                insert_data = {
                    "name": project.name,
                    "url": project.url,
                }
                self.dbo.insert_object("projects", insert_data, True)

        return True

    def delete_project(self, project_name: str) -> bool:
        query = Query()
        query.Delete("projects").Where("name = " + self.dbo.q(project_name))
        self.dbo.execute(query)
        self.dbo.commit()

        return self.dbo.get_num_rows() > 0
