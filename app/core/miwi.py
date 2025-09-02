import hashlib
from datetime import datetime, time, timedelta

import httpx
from fastapi import HTTPException

from app.config import get_config
from app.core.query import Query


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
        print(response)
        if response["Code"] == 0:
            return response
        elif response["Code"] == 1800:
            # Offline
            raise Warning("Device is offline")

        raise RuntimeError(response["Message"])
