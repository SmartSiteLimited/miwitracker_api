from wsgiref import headers

from fastapi import requests
from app.models.watch import API_ENDPOINT
from miwi import get_access_token
import httpx
from miwi import get_devices
import requests


def check_imei_exists(target_list) -> bool:
    url = "http://openapi.miwitracker.com//api/devicelist/get_devicelist"

    token = get_access_token()

    message = []

    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "UserId": 62186,
        "MapType": "Google"
    }

    r = httpx.post(url, headers=headers, json=payload, timeout=30.0)
    response = r.json()
    if response["Code"] == 0:
       device_list = get_devices()
       if not device_list:
           raise RuntimeError("No devices found")
    for item in target_list:
        if str(item) not in device_list:
            message.append(f"IMEI {item} does not exist in the online list.")

    if not message:
        message.append("No matching IMEI found.")

    return message

if __name__ == "__main__":
    # Example usage
    messages = []
    target_list = [
'889358866018679',
'860000030460736',
'860000038068523',
'889358866018588',
'860000030465131',
'860000027720274',
'860000038066568',
'889358866018658',
'889358866016652',
'889358866016684',
'860000027696839',
'889358866016660',
'860000038064480',
'889358866016618',
'860000038066329',
'860000030469570',
'889358866016617',
'889358866018693',
'860000030466139',
'889358866018678',
'860000030463292',
'860000027720233',
'860000027696870',  
'860000030458292',
'889358866018586'
]

    messages = check_imei_exists(target_list)
    for msg in messages:
        print(msg)
