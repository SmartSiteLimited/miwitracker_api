from app.schema.device import Device
from app.core import db
from app.core.db import Database, Query
from datetime import datetime
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

    def get_device_by_imei(self, imei: str) -> Device | None:
        query = Query()
        query.Select("*").From("devices").Where("imei = " + self.dbo.q(imei))
        self.dbo.execute(query)
        result = self.dbo.fetch_one()
        return Device(**result) if result else None
    
    async def save_device(self , payload , project): 

        if not project or payload.get("imeis") is None:
            raise ValueError("Project name is required when adding devices.")
        
        if payload.get("imeis"):
            imeis = payload.get("imeis", [])
            if not isinstance(imeis, list):
                imeis = [imei.strip() for imei in imeis.split(",") if imei.strip()]
            for imei in imeis:
                existing_device = self.get_device_by_imei(imei)
                if not existing_device:
                    insert_data = {
                        "imei": imei,
                        "project": project,
                        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    self.dbo.insert_object("devices", insert_data)
                else:
                    update_object = {
                        "imei": imei,
                        "project": project,
                        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    } 
                    self.dbo.update_object("devices", update_object, ["imei"], True)

            self.dbo.commit()
            return {"message": f"Added {len(imeis)} devices to project '{project}'."}

    def get_imei_by_project(self, project: str) -> list[str]:
        query = Query()
        query.Select("imei").From("devices").Where("project = " + self.dbo.q(project))
        self.dbo.execute(query)
        results = self.dbo.fetch_all()
        return [row["imei"] for row in results] if results else []
    
    def check_iccid_exists_by_imei(self, iccid: str , imei) -> bool:
        query = Query()
        query.Select("id").From("devices").Where("iccid = " + self.dbo.q(iccid)).Where("imei = " + self.dbo.q(imei))
        self.dbo.execute(query)
        result = self.dbo.fetch_one()
        return result is not None
    
    def get_devices_by_project(self, project: str) -> list[Device]:
        query = Query()
        query.Select("*").From("devices").Where("project = " + self.dbo.q(project))
        self.dbo.execute(query)
        results = self.dbo.fetch_all()
        return [Device(**row) for row in results] if results else []    