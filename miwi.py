import argparse
import hashlib
import json
import time
from pathlib import Path

import httpx

import config

API_ENDPOINT = "http://openapi.miwitracker.com"
APP_KEY = "09099902-464D-4DC2-BDED-D3AA242E9014"
APP_ID = 534
ACCESS_TOKEN = ""


def read_imeis(opt: argparse.Namespace):
    imeis = []

    if opt.imei:
        imeis.append(opt.imei)

    elif opt.file:
        file = Path(opt.file).resolve()
        if file.exists():
            with open(file) as f:
                for line in f:
                    imei = line.strip()
                    if imei:
                        imeis.append(imei)

    return imeis


def read_settings(file: str, type="json") -> dict:
    settings = {}

    file = Path(file).resolve()
    try:
        if file.exists():
            with open(file) as f:
                if type == "json":
                    settings = json.load(f)
                else:
                    settings = f.read()
            
    except ValueError:
        raise ValueError(f"Invalid settings: {file}")

    if not settings:
        raise ValueError(f"Settings not found: {file}")

    return settings


def get_access_token():
    global ACCESS_TOKEN
    if ACCESS_TOKEN:
        return ACCESS_TOKEN

    if (config.PROJECT_ROOT / "access_token.txt").exists():
        with open(config.PROJECT_ROOT / "access_token.txt") as f:
            ACCESS_TOKEN = f.readline().strip()

    if not ACCESS_TOKEN:
        token = fetch_token()
        with open(config.PROJECT_ROOT / "access_token.txt", "w") as f:
            f.write(token)

        ACCESS_TOKEN = token

    return ACCESS_TOKEN


def fetch_token():
    timestamp = int(time.time())
    password = APP_KEY + str(APP_ID) + str(timestamp)
    password_md5 = hashlib.md5(password.encode()).hexdigest()

    r = httpx.post(
        f"{API_ENDPOINT}/api/token/get_token",
        headers={"Content-Type": "application/json"},
        json={
            "AppId": APP_ID,
            "Password": password_md5,
            "Timestamp": timestamp
        }
    )

    response = r.json()
    if response:
        if response["Code"] == 0:
            return response["Result"]['AccessToken']

        raise RuntimeError(response["Message"])

    raise RuntimeError("Failed to fetch token")


def get_devices():
    url = f"{API_ENDPOINT}/api/devicelist/get_devicelist"

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
        online_devices = list(filter(lambda x: x["Status"] == 1, response["Result"]))
        return list(map(lambda x: x["Imei"], online_devices))

    return False


def send_command(payload: dict, timeout=15):
    url = f"{API_ENDPOINT}/api/command/sendcommand"

    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        r = httpx.post(url, headers=headers, json=payload, timeout=timeout)
        response = r.json()
        if response["Code"] == 0:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error setting block phone: {e}")
        return False



def send_batch_command(payload: dict, timeout=30):
    url = f"{API_ENDPOINT}/api/batchcmd/batchdevicecmdset"

    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    r = httpx.post(url, headers=headers, json=payload, timeout=timeout)
    response = r.json()
    if response["Code"] == 0:
        return response

    raise RuntimeError(response["Message"])


def read_imeis_by_file(file_name):
    imeis = []
        
    file = Path(file_name).resolve()
    if file.exists():
        with open(file) as f:
            for line in f:
                imei = line.strip()
                if imei:
                    imeis.append(imei)

    return imeis

def read_settings_by_file(file_name, type="json"):
    settings = {}

    file = Path(file_name).resolve()
    if file.exists():
        with open(file) as f:
            if type == "json":
                settings = json.load(f)
            else:
                settings = f.read()

    return settings
    
    