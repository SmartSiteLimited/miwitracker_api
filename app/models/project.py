from app.schema.project import projects
from app.core import db 
from app.core.db import Query
class Projects(): 
    def __init__(self):
        self.dbo = db.get_dbo()

    def get_projectId_by_name (self , project_name: str) -> int | None:
        query = Query()
        query.Select("id").From("projects").Where("name = " + self.dbo.q(project_name))
        self.dbo.execute(query)
        result = self.dbo.fetch_one()

        if result:
            project_id = result['id'] if 'id' in result else None
            return project_id
        return None

    def get_project_list(self) -> list[projects]:
        query = Query()
        query.Select("id", "name").From("projects")
        self.dbo.execute(query)
        results = self.dbo.fetch_all()
        return [projects(id=row[0], name=row[1]) for row in results] if results else []