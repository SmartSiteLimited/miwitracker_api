import hashlib
from datetime import datetime, timedelta
import httpx
import json 
from fastapi import HTTPException

from app.config import get_config
from app.core.query import Query
from app.models.projects import Projects
from app.models.settings import Settings
from app.models.devices import Devices
from app.core.db import get_dbo

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

            raise RuntimeError(response["Message"])

        raise RuntimeError("Failed to fetch token")

    async def get_devices(self, miwi_group_id=None):
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        payload = {"UserId": self.user_id, "MapType": "Google"}

        url = f"{self.api_endpoint}/api/devicelist/get_devicelist"
        if miwi_group_id:
            url = f"{self.api_endpoint}/api/devicelist/getdevicelistbygroup"
            payload.update({"GroupId": miwi_group_id})

        async with httpx.AsyncClient() as client:
            r = await client.post(url, headers=headers, json=payload, timeout=30.0)
        response = r.json()        
        if response["Code"] == 0:
            return response["Result"]

        raise HTTPException(status_code=400, detail="Failed to fetch devices")

    async def check_onlines(self, imeis: list[str] | None = None, miwi_group_id=None) -> bool:
        devices = await self.get_devices(miwi_group_id)
        online_devices = list(filter(lambda x: x["Status"] == 1 and x["Imei"] in imeis, devices))
        results = {imei: False for imei in (imeis or [])}

        for device in online_devices:
            if device["Imei"] in results:
                results[device["Imei"]] = True

        return results

    async def locate(self, imei: str) -> bool:
        try:
            response = await self.send_command({"Imei": imei, "CommandCode": "0039", "CommandValue": ""})
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

        raise RuntimeError(response["Message"])

    async def setPhoneBook(self, imei: str) -> bool:
        imei_info = Devices(self.dbo).get_device_by_imei(imei)
        if not imei_info:
            raise RuntimeError("Device not found")
        imei_project = imei_info.project
        settings = Settings(self.dbo).get_setting_by_projects(imei_project)
        if not settings:
            raise RuntimeError("Settings not found")
        phone_number_list = settings.get("phone_number", [])
        if not settings.get("phone_number"):
            raise RuntimeError("Phonebook settings not found")
        phone_book_settings = []
        for entry in phone_number_list:
            entry_number_list = entry.split(',')
            for entry in entry_number_list:
                new_entry = {
                    "Name": "SOS",
                    "Number": entry
                }    
                phone_book_settings.append(new_entry)
        settings_payload = json.dumps(phone_book_settings)
        try:
            response = await self.send_command({
                "Imei": imei,
                "CommandCode": "1106",
                "CommandValue": settings_payload
            })
            if response:
                update_object = {
                    "imei": imei,
                    'updated': datetime.now().isoformat()
                }
                self.dbo.update_object('devices', update_object, "imei")
        except Warning:
            return False
        
        return response["Code"] == 0
    async def setBlockPhone(self , imei: str) -> bool:
        timestamp = datetime.now().isoformat()
        try:
            response = await self.send_command(
                {"Imei": imei,
                 "timestamp": timestamp,
                 "CommandCode": "9601",
                 "CommandValue": "1"}
            )
            if response:
                update_object = {
                    "imei": imei,
                    'updated': datetime.now().isoformat()
                }
                self.dbo.update_object('devices', update_object, "imei")
        except Warning:
            return False
        
        return response["Code"] == 0
    async def setHealth(self, imei: str) -> bool:
        timestamp = datetime.now().isoformat()
        try:
            response = await self.send_command(
                {"Imei": imei,
                 "timestamp": timestamp,
                 "CommandCode": "2815",
                "CommandValue": '[{"TimeInterval":"300","Switch":"1"}]' 
                }
            )
            if response:
                update_object = {
                    "imei": imei,
                    'updated': datetime.now().isoformat()
                }
                self.dbo.update_object('devices', update_object, "imei")
        except Warning:
            return False
        
        return response["Code"] == 0
    
    async def setCallCenter(self , imei: str)-> bool:
        timestamp = datetime.now().isoformat()
        imei_info = Devices(self.dbo).get_device_by_imei(imei)
        project_name = imei_info.project if imei_info else None
        settings = Settings(self.dbo).get_setting_by_projects(project_name)
        if not settings:
            raise RuntimeError("Settings not found")
        call_center_number_list = settings.get("call_center_number")
        if not call_center_number_list:
            raise RuntimeError("Call center number not found")
        for call_center_number in call_center_number_list:
            try:
                response = await self.send_command(
                    {"Imei": imei,
                    "timestamp": timestamp,
                    "CommandCode": "9602",
                    "CommandValue": call_center_number}
                )
                if response:
                    update_object = {
                        "imei": imei,
                        'updated': datetime.now().isoformat()
                    }
                    self.dbo.update_object('devices', update_object, "imei")
            except Warning:
                return False

        return response["Code"] == 0
    
    async def setSoS(self , imei: str)->bool:
        timestamp = datetime.now().isoformat()
        try:
            response = await self.send_command(
                {"Imei": imei,
                 "timestamp": timestamp,
                 "CommandCode": "0001",
                 "CommandValue": "1"}
            )
            if response:
                update_object = {
                    "imei": imei,
                    'updated': datetime.now().isoformat()
                }
                self.dbo.update_object('devices', update_object, "imei")
        except Warning:
            return False

        return response["Code"] == 0
    
    
    async def get_groups_list(self):
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        payload = {"UserId": self.user_id, "MapType": "Google"}

        url = f"{self.api_endpoint}/api/organgroups/getorgangroupsinfolist"
        async with httpx.AsyncClient() as client:
            r = await client.post(url, headers=headers, json=payload, timeout=30.0)
        response = r.json()
        if response["State"] == 0:
            return response['Item']
        
    async def add_miwi_group(self , project: str):
        if not project:
            raise ValueError("Project name is required.")
        check_exist_group_by_project = Projects(self.dbo).check_group_id_exists_by_project(project)
        if check_exist_group_by_project:
            return {"message": f"Group for project '{project}' already exists with Group ID {check_exist_group_by_project}."}
        
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        payload = {"UserId": self.user_id, "GroupName": project ,"Description":""}

        url = f"{self.api_endpoint}/api/organgroups/addorgangroupsinfo"
        async with httpx.AsyncClient() as client:
            r = await client.post(url, headers=headers, json=payload, timeout=30.0)
        response = r.json()
        if response["State"] == 0:
            url = f"{self.api_endpoint}/api/organgroups/getorgangroupsinfolist"
            async with httpx.AsyncClient() as client:
                r = await client.post(url, headers=headers, json={"UserId": self.user_id}, timeout=30.0)
                response = r.json()
                if response["State"] == 0:
                    for item in response['Item']:
                        if item.get("GroupName") == project:
                            group_id = item.get("GroupId")
                            update_project_data = {
                                "name": project,
                                "miwi_group_id": group_id,
                            }
                            self.dbo.update_object("projects", update_project_data, ["name"], True)
                            return {"message": f"Group for project '{project}' added successfully with Group ID {group_id}."}
            
        

                        
    async def update_group_id_for_imei(self , group_id , project):
        if not project or not group_id:
            raise ValueError("Project name and Group ID are required.")
        
        device = Devices(self.dbo)  
        # imeis_list = device.get_imei_by_project(project)
        device_list_by_project = device.get_devices_by_project(project)
        if not device_list_by_project:
            raise ValueError(f"No devices found for project '{project}'.")
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        payload = {"UserId": self.user_id }

        filter_device__list = list(filter(lambda x: not x.miwi_group_id or x.miwi_group_id != group_id, device_list_by_project))
        filter_imeis_list = [d.imei for d in filter_device__list]
        filter_imeis_string = ",".join(filter_imeis_list)
        
        # print(f"Filtered IMEIs without group ID: {filter_imeis_string}")
        url = f"{self.api_endpoint}/api/organgroups/movedevicestoorgangroups"
        payload.update({"GroupId": group_id , "Imeis":filter_imeis_string})
        async with httpx.AsyncClient() as client:
            r = await client.post(url, headers=headers, json=payload, timeout=30.0)
            response = r.json()
            if response["State"] == 0:          
                for imei in filter_imeis_list:
                    existing_device = Devices(self.dbo).get_device_by_imei(imei)
                    if existing_device and existing_device.miwi_group_id != group_id:
                        # print(f"Updating Group ID for IMEI {imei} to {group_id}")
                        update_data = {
                            "imei": imei,
                            "project": project,
                            "miwi_group_id": group_id,
                            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                        self.dbo.update_object("devices", update_data, ["imei"], True)  
    
    async def update_iccid(self , miwi_group_id):
        get_devices = await self.get_devices(miwi_group_id)
        for device in get_devices:
            imei = device.get("Imei")
            iccid = device.get("Imsi")
            if imei and iccid:
                existing_device = Devices(self.dbo).get_device_by_imei(imei)
                if existing_device and existing_device.iccid != iccid:
                    update_data = {
                        "imei": imei,
                        "iccid": iccid,
                        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    self.dbo.update_object("devices", update_data, ["imei"], True)
                    
    async def add_update_group_and_icc(self , project: str):
        group_id = Projects(self.dbo).check_group_id_exists_by_project(project)
                #add the device to the group in miwi
        if group_id:
            await self.update_group_id_for_imei(group_id , project)
            await self.update_iccid(group_id)
            return {"message": f"Group ID for project '{project}' updated successfully to {group_id}."}
        
        return {"message": f"Group ID for project '{project}' is already set to {group_id}."}
    
    async def get_group_list(self):
        url = f"{self.api_endpoint}/api/organgroups/getorgangroupsinfolist"
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        payload = {"UserId": self.user_id}
        async with httpx.AsyncClient() as client:
            r = await client.post(url, headers=headers, json=payload, timeout=30.0)
            response = r.json()
            if response["State"] == 0:
                return response["Item"]
            return []
        
    async def delete_group(self , group_id , project):
        if not group_id or not project :
            raise ValueError("Group ID is required.")
        
        url = f"{self.api_endpoint}/api/organgroups/delorgangroupsinfo"
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        payload = {"UserId": self.user_id, "GroupId": group_id}
        async with httpx.AsyncClient() as client:
            r = await client.post(url, headers=headers, json=payload, timeout=30.0)
            response = r.json()
            if response["State"] == 0:
                update_project_data = {
                    "name": project,
                    "miwi_group_id": None,
                }
                self.dbo.update_object("projects", update_project_data, "name", True)
                return {"message": f"Group ID '{group_id}' deleted successfully."}
            return {"message": f"Failed to delete Group ID '{group_id}'. Reason: {response.get('Message', 'Unknown error')}"}