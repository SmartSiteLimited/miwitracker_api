from datetime import datetime

import httpx

from app.config import get_config
from app.core.db import Database, Query
from app.schema.device import Device


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
            search_conditions = (
                []
                + [f"{field} LIKE '%{filters['search']}'" for field in searchable]
                + [f"{field} LIKE '{filters['search']}%'" for field in searchable]
            )
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

    async def save_device(self, payload, project):
        if not project or payload.get("imeis") is None:
            raise ValueError("Project name is required when adding devices.")

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
        return True

    def get_imei_by_project(self, project: str) -> list[str]:
        query = Query()
        query.Select("imei").From("devices").Where("project = " + self.dbo.q(project))
        self.dbo.execute(query)
        results = self.dbo.fetch_all()
        return [row["imei"] for row in results] if results else []

    def check_iccid_exists_by_imei(self, iccid: str, imei) -> bool:
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

    async def fetch_new_devices(self, project: str) -> list[Device]:
        # fetch the json data from the platform
        fetch_url = get_config("miwitracker.fetch_device_url")

        data = {
            "project": project,
        }

        # set no cert verify
        response = httpx.post(fetch_url, verify=False, json=data, timeout=10)
        if response.status_code != 200:
            raise ValueError("Failed to fetch data from the platform.")

        resp = response.json()
        if not resp.get("success"):
            raise ValueError("Failed to fetch data from the platform: " + resp.get("message", "Unknown error"))

        devices_data = resp.get("data", {})

        # collect IMEIs from platform response
        new_imeis = set()
        for imei, title in devices_data.items():
            if imei and isinstance(imei, str) and imei.strip():
                new_imeis.add(imei.strip())

        # existing IMEIs in the DB for this project
        existing_imeis = set(self.get_imei_by_project(project))

        # insert or update devices from the fetched list
        for imei in new_imeis:
            existing_device = self.get_device_by_imei(imei)
            if not existing_device:
                insert_data = {
                    "imei": imei,
                    "project": project,
                    "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                if self.dbo.insert_object("devices", insert_data):
                    print(f"Inserted new device with IMEI: {imei}")
            else:
                update_object = {
                    "imei": imei,
                    "project": project,
                    "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                if self.dbo.update_object("devices", update_object, ["imei"], True):
                    print(f"Updated existing device with IMEI: {imei}")

        # delete devices that exist in DB but were not present in the fetched list
        to_delete = existing_imeis - new_imeis
        for imei in to_delete:
            query = Query()
            query.Delete("devices").Where("imei = " + self.dbo.q(imei)).Where("project = " + self.dbo.q(project))
            self.dbo.execute(query)
            print(f"Deleted device with IMEI: {imei}")

        # commit all changes and return current devices for the project
        self.dbo.commit()
        return self.get_devices_by_project(project)
