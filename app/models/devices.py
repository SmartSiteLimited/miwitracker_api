from app.schema.device import Device
from app.core import db
from app.core.db import Database, Query


class Devices:
    def __init__(self, dbo: Database):
        self.dbo = dbo

    def get_devices(self, project: str, filters: dict[str, any]) -> list[Device]:
        query = Query()
        query.Select("*").From("devices")

        if filters.get("id"):
            query.Where("id = " + int(filters["id"]))
        elif filters.get("imei"):
            query.Where("imei = '" + filters["imei"] + "'")
        elif filters.get("imeis"):
            query.Where("imei IN (" + ",".join([self.dbo.q(imei) for imei in filters["imeis"]]) + ")")
        else:
            query.Where("project = " + self.dbo.q(project))

        if filters.get("search"):
            searchable = ["imei", "iccid"]
            search_conditions = [] + \
                [f"{field} LIKE '%{filters['search']}'" for field in searchable] + \
                [f"{field} LIKE '{filters['search']}%'" for field in searchable]
            query.Where("(" + " OR ".join(search_conditions) + ")")

        self.dbo.execute(query)
        results = self.dbo.fetch_all()

        return [Device(**row) for row in results] if results else []
