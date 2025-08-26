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
'889358866015361',
'889358866009957',
'998855661062786',
'860000030476377',
'860000018193655',
'889358866009422',
'889358866009046',
'860000017102228',
'860000018153451',
'889358866006966',
'860000030461130',
'860000038071006',
'860000030470537',
'860000017101907',
'860000027739670',
'860000029498432',
'998855661071416',
'860000018157494',
'889358866007782',
'860000027738110',
'889358866006572',
'358800026176355',
'860000030464373',
'860000038064407',
'358800026017278',
'860000027697159',
'860000038069687',
'860000038132964',
'860000030468739',
'860000030459134',
'860000030458938',
'860000038067764',
'860000038134929',
'860000038065008',
'860000038133400',
'860000030459738',
'860000030459530',
'860000030462534',
'860000030470370',
'860000030458532',
'860000038065446',
'860000038065081',
'889358866018594',
'860000030462856',
'860000027720837',
'358800026016999',
'860000030468416',
'860000030459894',
'358800026341553',
'860000030464217'
]

    messages = check_imei_exists(target_list)
    for msg in messages:
        print(msg)
