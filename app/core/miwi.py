import hashlib
import json
from datetime import datetime, timedelta

import httpx
from fastapi import HTTPException

from app.config import get_config
from app.core.query import Query
from app.models.devices import Devices
from app.models.projects import Projects
from app.models.settings import Settings


class Miwi:
    def __init__(self, dbo):
        self.dbo = dbo

        miwi_config = get_config("miwitracker")
        self.app_id = miwi_config.get("app_id", "")
        self.app_key = miwi_config.get("app_key", "")
        self.api_endpoint = miwi_config.get("api_endpoint", "")
        self.user_id = miwi_config.get("user_id", "")

        self.access_token = ""
        self.load_token()

    def load_token(self):
        query = Query()
        query.Select("*").From("caches").Where("`key` = 'miwi.access_token'")
        self.dbo.execute(query)
        record = self.dbo.fetch_one()

        # treat as expire if last_updated is more than 2 weeks
        if record:
            last_updated = record["last_updated"]
            if last_updated < datetime.now() - timedelta(weeks=2):
                record = None
            else:
                self.access_token = str(record["value"])

        if not record:
            self.access_token = self.fetch_token()
            insert_data = {
                "key": "miwi.access_token",
                "value": self.access_token,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            self.dbo.insert_object("caches", insert_data, True)

    def fetch_token(self):
        timestamp = int(datetime.now().timestamp())
        password = self.app_key + str(self.app_id) + str(timestamp)
        password_md5 = hashlib.md5(password.encode()).hexdigest()

        r = httpx.post(
            f"{self.api_endpoint}/api/token/get_token",
            headers={"Content-Type": "application/json"},
            json={"AppId": self.app_id, "Password": password_md5, "Timestamp": timestamp},
        )

        response = r.json()
        if response:
            if response["Code"] == 0:
                return response["Result"]["AccessToken"]

            raise HTTPException(status_code=400, detail=response["Message"])

        raise HTTPException(status_code=400, detail="Failed to fetch token")

    async def get_devices(self, miwi_group_id=None):
        # headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        payload = {"UserId": self.user_id, "MapType": "Google"}

        url = "/api/devicelist/get_devicelist"
        if miwi_group_id:
            url = "/api/devicelist/getdevicelistbygroup"
            payload.update({"GroupId": miwi_group_id})

        response = await self.request(url, payload, "POST")
        if response["Code"] == 0:
            return response["Result"]

        raise HTTPException(status_code=400, detail="Failed to fetch devices")

    async def check_onlines(self, imeis: list[str] | None = None, miwi_group_id=None) -> bool:
        devices = await self.get_devices(miwi_group_id)
        online_devices = list(filter(lambda x: x["Status"] == 1 and x["Imei"] in imeis, devices))
        results = dict.fromkeys(imeis or [], False)

        for device in online_devices:
            if device["Imei"] in results:
                results[device["Imei"]] = True

        return results

    async def turn_on(self, imei: str, level=8) -> bool:
        timestamp = datetime.now().isoformat()
        payload = {"Imei": imei, "timestamp": timestamp, "CommandCode": "9203", "CommandValue": "1,1"}

        if await self.send_command(payload):
            timestamp = datetime.now().isoformat()
            payload = {"Imei": imei, "timestamp": timestamp, "CommandCode": "9722", "CommandValue": str(level)}
            return await self.send_command(payload)

        return False

    async def turn_off(self, imei: str) -> bool:
        timestamp = datetime.now().isoformat()
        payload = {"Imei": imei, "timestamp": timestamp, "CommandCode": "9203", "CommandValue": "0,0"}
        return await self.send_command(payload)

    async def locate(self, imei: str) -> bool:
        try:
            response = await self.send_command({"Imei": imei, "CommandCode": "0039", "CommandValue": ""})
        except Warning:
            return False

        return response["Code"] == 0

    async def set_fall_alert(self, imei: str, project) -> bool:
        try:
            setting = Settings(self.dbo).get_by_project(project)
            if not setting or not setting.get("sensitivity"):
                level = 8
            else:
                level_list = setting.get("sensitivity")
                # get the first item if it's a list
                level = int(level_list[0])
            response = await self.turn_on(imei, level)
            if response:
                update_data = {"imei": imei, "updated": datetime.now().isoformat()}
                self.dbo.update_object("devices", update_data, "imei")
        except Warning:
            return False

        return response["Code"] == 0

    async def send_command(self, payload: dict, timeout=15):
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.api_endpoint}/api/command/sendcommand", headers=headers, json=payload, timeout=timeout
            )
        response = r.json()
        if response["Code"] == 0:
            return response
        elif response["Code"] == 1800:
            # Offline
            raise Warning("Device is offline")

        raise HTTPException(status_code=400, detail=response.get("Message", "Request failed"))

    async def request(self, uri: str, payload: dict, method="POST"):
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

        async with httpx.AsyncClient() as client:
            if method.upper() == "POST":
                r = await client.post(f"{self.api_endpoint}{uri}", headers=headers, json=payload, timeout=30.0)
            else:
                r = await client.get(f"{self.api_endpoint}{uri}", headers=headers, params=payload, timeout=30.0)
        response = r.json()
        if ("Code" in response and response["Code"] == 0) or ("State" in response and response["State"] == 0):
            return response

        raise HTTPException(status_code=400, detail=response.get("Message", "Request failed"))

    async def set_phone_book(self, imei: str) -> bool:
        device = Devices(self.dbo).get_device_by_imei(imei)
        if not device:
            raise ValueError(status_code=404, detail="Device not found")

        settings = Settings(self.dbo).get_by_project(device.project)
        if not settings:
            raise ValueError(status_code=404, detail="Settings not found")

        sos_phone_numbers = settings.get("sos_phone_number", [])
        if not sos_phone_numbers:
            raise ValueError("Phonebook settings not found")

        phone_book_settings = []
        for entry in sos_phone_numbers:
            entry_number_list = entry.split(",")
            for entry in entry_number_list:
                new_entry = {"Name": "SOS", "Number": entry}
                phone_book_settings.append(new_entry)
        settings_payload = json.dumps(phone_book_settings)
        try:
            response = await self.send_command({"Imei": imei, "CommandCode": "1106", "CommandValue": settings_payload})
            if response:
                update_data = {"imei": imei, "updated": datetime.now().isoformat()}
                self.dbo.update_object("devices", update_data, "imei")
        except Warning:
            return False

        return response["Code"] == 0

    async def set_block_phone(self, imei: str) -> bool:
        timestamp = datetime.now().isoformat()
        try:
            response = await self.send_command(
                {"Imei": imei, "timestamp": timestamp, "CommandCode": "9601", "CommandValue": "1"}
            )
            if response:
                update_data = {"imei": imei, "updated": datetime.now().isoformat()}
                self.dbo.update_object("devices", update_data, "imei")
        except Warning:
            return False

        return response["Code"] == 0
    
    async def set_bodytemp(self, imei: str):
        timestamp = datetime.now().isoformat()

        payload = {
            "Imei": imei,
            "Time": timestamp,
            "CommandCode": "9113",
            "CommandValue": '1,1'
        }
        try :
            response = await self.send_command(payload)
            if response:
                update_data = {"imei": imei, "updated": datetime.now().isoformat()}
                self.dbo.update_object("devices", update_data, "imei")
        except Warning:
            return False

    async def set_gpstrack(self, imei: str):
        timestamp = datetime.now().isoformat()

        payload = {
            "Imei": imei,
            "Time": timestamp,
            "CommandCode": "0305",
            "CommandValue": '10'
        }        
        try :
            response = await self.send_command(payload)
            if response:
                update_data = {"imei": imei, "updated": datetime.now().isoformat()}
                self.dbo.update_object("devices", update_data, "imei")
        except Warning:
            return False
        
    async def set_health_command(self, imei: str) -> bool:
        timestamp = datetime.now().isoformat()
        try:
            payload = {
                "Imei": imei,
                "timestamp": timestamp,
                "CommandCode": "2815",
                "CommandValue": '[{"TimeInterval":"300","Switch":"1"}]',
            }
            response = await self.send_command(payload)
            if response:
                update_data = {"imei": imei, "updated": datetime.now().isoformat()}
                self.dbo.update_object("devices", update_data, "imei")
        except Warning:
            return False
        

    async def set_health(self, imei: str) -> bool:
        timestamp = datetime.now().isoformat()
        
        await self.set_bodytemp(imei)
        await self.set_gpstrack(imei)
        await self.set_health_command(imei)

        return True

    async def set_call_center(self, imei: str) -> bool:
        device = Devices(self.dbo).get_device_by_imei(imei)
        if not device:
            raise ValueError("Device not found")

        timestamp = datetime.now().isoformat()
        settings = Settings(self.dbo).get_by_project(device.project)
        if not settings or not settings.get("call_center_number"):
            raise ValueError("Settings not found")

        call_center_number_list = settings.get("call_center_number")
        if not call_center_number_list:
            raise ValueError("Call center number not found")

        for call_center_number in call_center_number_list:
            try:
                payload = {
                    "Imei": imei,
                    "timestamp": timestamp,
                    "CommandCode": "9602",
                    "CommandValue": call_center_number,
                }
                response = await self.send_command(payload)
                if response:
                    update_data = {"imei": imei, "updated": datetime.now().isoformat()}
                    self.dbo.update_object("devices", update_data, "imei")
            except Warning:
                return False

        return response["Code"] == 0

    async def off_fall_alert(self, imei: str) -> bool:
        timestamp = datetime.now().isoformat()
        try:
            response = await self.turn_off(imei)
            if response:
                update_data = {"imei": imei, "updated": timestamp}
                self.dbo.update_object("devices", update_data, "imei")
        except Warning:
            return False

        return response["Code"] == 0

    async def set_sos(self, imei: str) -> bool:
        timestamp = datetime.now().isoformat()
        device = Devices(self.dbo).get_device_by_imei(imei)
        if not device:
            raise ValueError("Device not found")
        settings = Settings(self.dbo).get_by_project(device.project)
        if not settings or not settings.get("sos_phone_number"):
            raise ValueError("Settings not found")
        sos_phone_number_list = settings.get("sos_phone_number")
        # convert to list as ["abc"] or ["abc","def"]
        if isinstance(sos_phone_number_list, str):
            sos_phone_number_list = [num.strip() for num in sos_phone_number_list.split(",") if num.strip()]
        for number in sos_phone_number_list:
            try:
                payload = {"Imei": imei, "timestamp": timestamp, "CommandCode": "0001", "CommandValue": number}
                response = await self.send_command(payload)
                if response:
                    update_data = {"imei": imei, "updated": datetime.now().isoformat()}
                    self.dbo.update_object("devices", update_data, "imei")
            except Warning:
                return False

        return response["Code"] == 0

    async def reboot(self, imei: str) -> bool:
        timestamp = datetime.now().isoformat()
        try:
            payload = {"Imei": imei, "timestamp": timestamp, "CommandCode": "0010", "CommandValue": ""}
            response = await self.send_command(payload)
        except Warning:
            return False

        return response["Code"] == 0

    async def power_off(self, imei: str) -> bool:
        timestamp = datetime.now().isoformat()
        try:
            payload = {"Imei": imei, "timestamp": timestamp, "CommandCode": "0048", "CommandValue": ""}
            response = await self.send_command(payload)
        except Warning:
            return False

        return response["Code"] == 0

    async def get_group_list(self):
        payload = {"UserId": self.user_id, "MapType": "Google"}

        response = await self.request("/api/organgroups/getorgangroupsinfolist", payload, "POST")
        return response.get("Item", [])

    async def create_group(self, project: str, description=""):
        if not project:
            raise ValueError("Project name is required.")

        group_id = Projects(self.dbo).get_project_group_id(project)
        if group_id:
            raise ValueError(f"Group for project '{project}' already exists with Group ID {group_id}.")

        payload = {"UserId": self.user_id, "GroupName": project, "Description": description}

        response = await self.request("/api/organgroups/addorgangroupsinfo", payload, "POST")
        # call get_group_list to get the new group id
        groups = await self.get_group_list()
        new_group_id = [item.get("GroupId") for item in groups if item.get("GroupName") == project]
        if new_group_id:
            group_id = new_group_id[0]
            update_project_data = {
                "name": project,
                "miwi_group_id": group_id,
            }
            self.dbo.update_object("projects", update_project_data, ["name"], True)

        return True

    async def update_group_id_for_imei(self, group_id: int, project: str):
        if not project or not group_id:
            raise ValueError("Project name and Group ID are required.")

        device = Devices(self.dbo)

        project_devices = device.get_devices_by_project(project)
        if not project_devices:
            raise ValueError(f"No devices found for project '{project}'.")

        payload = {"UserId": self.user_id}

        filter_device_list = list(filter(lambda x: not x.miwi_group_id or x.miwi_group_id != group_id, project_devices))
        filter_imeis_list = [d.imei for d in filter_device_list]
        filter_imeis_string = ",".join(filter_imeis_list)
        payload.update({"GroupId": group_id, "Imeis": filter_imeis_string})

        response = await self.request("/api/organgroups/movedevicestoorgangroups", payload, "POST")
        for imei in filter_imeis_list:
            existing_device = Devices(self.dbo).get_device_by_imei(imei)
            if existing_device and existing_device.miwi_group_id != group_id:
                update_data = {
                    "imei": imei,
                    "project": project,
                    "miwi_group_id": group_id,
                    "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                self.dbo.update_object("devices", update_data, ["imei"], True)

        return True

    async def update_iccid(self, miwi_group_id):
        group_devices = await self.get_devices(miwi_group_id)
        if not group_devices:
            return 0

        devices_model = Devices(self.dbo)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        updates = []
        for device in group_devices:
            imei = device.get("Imei")
            iccid = device.get("Imsi")
            if not imei or not iccid:
                continue

            existing_device = devices_model.get_device_by_imei(imei)
            if existing_device and (existing_device.iccid != iccid):
                updates.append({"imei": imei, "iccid": iccid, "updated": now})

        for upd in updates:
            self.dbo.update_object("devices", upd, ["imei"], True)

        return True

    async def update_group_and_iccid(self, project: str):
        group_id = Projects(self.dbo).get_project_group_id(project)
        if group_id:
            await self.update_group_id_for_imei(group_id, project)
            await self.update_iccid(group_id)

            return True

        raise ValueError(f"No group ID found for project '{project}'.")

    async def delete_group(self, group_id: str):
        if group_id:
            # get project by group_id
            project = ""
            query = Query()
            query.Select("name").From("projects").Where("miwi_group_id = " + self.dbo.q(str(group_id)))
            self.dbo.execute(query)
            result = self.dbo.fetch_one()
            project = result["name"] if result else ""

            payload = {"UserId": self.user_id, "GroupId": group_id}

            await self.request("/api/organgroups/delorgangroupsinfo", payload, "POST")

            if project:
                update_project_data = {
                    "name": project,
                    "miwi_group_id": None,
                }
                self.dbo.update_object("projects", update_project_data, "name", True)

            return True

        raise ValueError(f"No group ID found for project '{project}'.")
