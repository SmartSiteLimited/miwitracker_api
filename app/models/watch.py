from datetime import date, datetime
from itertools import count
from app.schema.watch import Watch
from app.core import db 
from app.core.db import Query
import requests
import json
import time
from typing import List
from miwi import get_access_token
import miwi
import set_fallalert as alert
import httpx
import config
from app.models.settings import SettingFieldValue
API_ENDPOINT = "http://openapi.miwitracker.com"
APP_KEY = "09099902-464D-4DC2-BDED-D3AA242E9014"
APP_ID = 534
ACCESS_TOKEN = get_access_token()
timestamp = int(time.time() * 1000) 

class WatchItems(): 
        def __init__(self):
            self.watches = []

        def get_watches_by_project(self , project_name:str , created: str | None = None) -> list[Watch]:
            dbo = db.get_dbo()
            query = Query()
            query.Select('*').From('watches').Where('project = ' +  dbo.q(project_name) )
            if created:
                query.Where('created <= ' + dbo.q(created))
            dbo.execute(str(query))
            result = dbo.fetch_all()
            if not result:
                return []
            return [Watch(**item) for item in result]

        def get_online_imeis_by_project(self , project_name:str , created: str | None = None) -> list[Watch]:
            dbo = db.get_dbo()
            query = Query()
            query.Select('*').From('watches').Where('project = ' +  dbo.q(project_name) + ' AND `online_status` = 1')
            if created:
                query.Where('created <= ' + dbo.q(created))
            dbo.execute(str(query))
            result = dbo.fetch_all()
            return [Watch(**item) for item in result]

        def get_project_list(self) -> list[str]:
            dbo = db.get_dbo()
            query = Query()
            query.Select('DISTINCT project').From('watches').Where('online_status = 1')
            dbo.execute(str(query))
            result = dbo.fetch_all()
            return [item['project'] for item in result]

        def check_online_by_api(self, project_name: str , created: str | None = None) -> bool:
            results = []
            dbo = db.get_dbo()
            imei_list = self.get_online_imeis_by_project(project_name, created)
            if not imei_list:
                return []
            online_imeis = miwi.get_devices()
            for imei in imei_list:
                if imei.IMEI_id in online_imeis:
                    results.append(imei)                
                    #update the status of the watch to online
                    update_object = {
                        "IMEI_id": imei.IMEI_id,
                        'online_status': 1,
                        'updated': datetime.now().isoformat()
                    }
                    dbo.update_object('watches', update_object, "IMEI_id")
                else :
                    #update the status of the watch to offline
                    update_object = {
                        "IMEI_id": imei.IMEI_id,
                        'online_status': 0,
                        'updated': datetime.now().isoformat()
                    }
                    dbo.update_object('watches', update_object, "IMEI_id")
            return results

        def fetch_watches_from_api(self) ->List[Watch]:
            dbo = db.get_dbo()
            try:
                target_project = [
                    "hy202204",
                    "nl202006",
                    "cv202103",
                    "bktc",
                    "nd202202",
                    "hy201802",
                    "ed202101",
                    "ge202104",
                    "ed202202",
                    "hy202409",
                    "hy202008"
                ]
                for project in target_project:
                    api_url = f"https://{project}.monitor.com.hk/index.php?option=com_ems&task=miwitracker.getRegDevices&format=json"
                    try:
                        # Get the JSON data from the API
                        response = requests.get(api_url)
                        response.raise_for_status()
                        if response.status_code == 200:
                            response_text = response.json()
                            datas = response_text.get('data', [])
                        else:
                            print(f"Failed to fetch data for project {project}. Status code: {response.status_code}")
                            continue

                        # Log the response for debugging
                        print(f"API response for {project}: {response_text}")

                        # Check if datas is iterable (list or dict) or handle other cases
                        if isinstance(datas, dict):
                            # Handle dictionary response (like hy202204)
                            print('running dict')
                            for imei_id in datas.keys():
                                # Ensure imei_id is a string for consistency
                                imei_id_str = str(imei_id)
                                query = Query()
                                query.Select('id').From('watches').Where(f'IMEI_id = {dbo.q(imei_id_str)}')
                                print(query)
                                dbo.execute(str(query))
                                result = dbo.fetch_one()
                                id = result['id'] if result else None
                                print(f"Processing IMEI: {imei_id_str}, ID: {id}")
                                if not result:
                                    print('insert new one')
                                    # Insert new watch
                                    inserted_object = {
                                        'IMEI_id': imei_id_str,
                                        'project': project,
                                        'created': datetime.now().isoformat(),
                                        'updated': None
                                    }
                                    dbo.insert_object('watches', inserted_object)
                                else:
                                    print('update existing one')
                                    update_object = {
                                        "id": id,
                                        'updated': datetime.now().isoformat()
                                    }
                                    dbo.update_object('watches', update_object, "id")
                        elif isinstance(datas, list):
                            # Handle list response
                            print('running list')
                            for item in datas:
                                if isinstance(item, dict):
                                    for imei_id in item.keys():
                                        query = Query()
                                        query.Select('id').From('watches').Where(f'IMEI_id = {dbo.q(str(imei_id))}')
                                        print(query)
                                        dbo.execute(str(query))
                                        result = dbo.fetch_one()
                                        if not result:
                                            inserted_object = {
                                                'IMEI_id': str(imei_id),
                                                'project': project,
                                                'created': datetime.now().isoformat(),
                                            }
                                            dbo.insert_object('watches', inserted_object)
                                        else:
                                            id = result.get('id')
                                            update_object = {
                                                "id": id,
                                                'updated': datetime.now().isoformat()
                                            }
                                            dbo.update_object('watches', update_object, id)
                                elif isinstance(item, str):
                                    imei_id = item
                                    if not imei_id:
                                        continue
                                    query = Query()
                                    query.Select('id').From('watches').Where(f'IMEI_id = {dbo.q(imei_id)}')
                                    dbo.execute(str(query))
                                    result = dbo.fetch_one()
                                    if not result:
                                        inserted_object = {
                                            'IMEI_id': imei_id,
                                            'project': project,
                                            'online_status': 1,
                                            'created': datetime.now().isoformat(),
                                            'updated': datetime.now().isoformat()
                                        }
                                        dbo.insert_object('watches', inserted_object)
                                    else:
                                        id = result.get('id')
                                        update_object = {
                                            "id" : id,
                                            'online_status': 1,
                                            'updated': datetime.now().isoformat()
                                        }
                                        dbo.update_object('watches', update_object, "id")
                        else:
                            print(f"No iterable data found for project {project}. Received: {datas}")
                            continue

                    except requests.exceptions.RequestException as e:
                        print(f"Request error for project {project}: {e}")
                        continue

            except Exception as e:
                print(f"Error fetching watches from API: {e}")
                return []
            return []  # Adjust return based on actual requirements


        def set_block_phone (self, project_name: str, switch: bool = True , created: str | None = None) -> bool:
            message = []
            dbo = db.get_dbo()
            try:

                imeis_list = self.get_online_imeis_by_project(project_name, created)
                if not imeis_list:
                    return False
                for imei in imeis_list:
                    payload = {
                        "Imei": imei.IMEI_id,
                        "timestamp": timestamp,
                        "CommandCode": "9601",
                        "CommandValue": "1" if switch else "0"
                    }
                    response = miwi.send_command(payload)
                    if response:
                        message.append(f"Block phone for {imei.IMEI_id} set to {switch}")
                        
                        update_object = {
                            "IMEI_id": imei.IMEI_id,
                            "updated": datetime.now().isoformat()
                        }
                        dbo.update_object('watches', update_object, "IMEI_id")
                        
                    else:   
                        message.append(f"Failed to set block phone for {imei.IMEI_id}")

                return message
            except Exception as e:
                print(f"Error setting block phone: {e}")
                return False
            
            
        def set_health (self , project : str, created: str | None = None):
            message = []
            dbo = db.get_dbo()
            try:
                imeis = self.get_online_imeis_by_project(project, created)
                if not imeis:
                    return False
                for imei in imeis:
                    payload = {
                        "Imei": imei.IMEI_id,
                        "timestamp": timestamp,
                        "CommandCode": "2815",
                        "CommandValue": '[{"TimeInterval":"300","Switch":"1"}]'
                    }
                    response = miwi.send_command(payload)
                    if response:
                        message.append(f"Health for {imei.IMEI_id} set")
                        update_object = {
                            "IMEI_id": imei.IMEI_id,
                            "updated": datetime.now().isoformat()
                        }
                        dbo.update_object('watches', update_object, "IMEI_id")
                    else:
                        message.append(f"Failed to set health for {imei.IMEI_id}")

                return message
            except Exception as e:
                print(f"Error setting health: {e}")
                return False

        def set_callcenter (self, project: str , created : str | None = None , settings: list[str] | None = None):

            message = []
            dbo = db.get_dbo()
            
            imeis_list = self.get_online_imeis_by_project(project , created)
            if not imeis_list:
                return False

            for imei in imeis_list:
                if settings:
                    for entry in settings:
                        if not isinstance(entry, str):
                            continue
                        payload = {
                            "Imei": imei.IMEI_id,
                            "timestamp": timestamp,
                            "CommandCode": "0009",
                            "CommandValue": entry
                        }
                        response = miwi.send_command(payload)
                        if response:
                            message.append(f"Call center for {imei.IMEI_id} set to {entry}")
                            update_object = {
                            "IMEI_id": imei.IMEI_id,
                            "updated": datetime.now().isoformat()
                            }
                            dbo.update_object('watches', update_object, "IMEI_id")

                            
                        else:
                            message.append(f"Failed to set call center for {entry.get('Imei')}")

            return message

        def set_sos(self, project: str , created : str  | None = None , settings: List[str] | None = None):

            imeis_list = self.get_online_imeis_by_project(project , created)
            message = []
            dbo = db.get_dbo()
            if not imeis_list:
                return False
            for imei in imeis_list:
                if not settings:
                    message.append(f"No call center number found for {imei.IMEI_id}")
                    continue
                
                for entry in settings:
                    payload = {
                        "Imei": imei.IMEI_id,
                        "timestamp": timestamp,
                        "CommandCode": "0001",
                        "CommandValue": entry
                    }
                    response = miwi.send_command(payload)
                    if response:
                        message.append(f"SOS for {imei.IMEI_id} set to number {entry}")
                        update_object = {
                            "IMEI_id": imei.IMEI_id,
                            'updated': datetime.now().isoformat()
                        }
                        dbo.update_object('watches', update_object, "IMEI_id")
                    else:
                        message.append(f"Failed to set SOS for {imei.IMEI_id}")

            return message

        def set_phonebook(self, project: str , created : str  | None = None , settings: list[str] | None = None):

            imeis_list = self.get_online_imeis_by_project(project , created)
            if not imeis_list:
                return False
            
            message = []
            dbo = db.get_dbo()
            try:
                for imei in imeis_list:
                    if not settings:
                        message.append(f"No phone numbers found for {imei.IMEI_id}")
                        continue
                    
                        #convert the entry to a json format settings 
                    phone_book_setting = []
                    for entry in settings:
                        new_entry = {
                            "Name": "SOS",
                            "Phone": entry
                        }
                        phone_book_setting.append(new_entry)
                    settings_payload = json.dumps(phone_book_setting) 
                    payload = {
                        "Imei": imei.IMEI_id,
                        "timestamp": timestamp,
                        "CommandCode": "1106",
                        "CommandValue": settings_payload
                    }
                    response = miwi.send_command(payload)
                    if response:
                        message.append(f"Phonebook for {imei.IMEI_id} set")
                        update_object = {
                            "IMEI_id": imei.IMEI_id,
                            'updated': datetime.now().isoformat()
                        }
                        dbo.update_object('watches', update_object, "IMEI_id")

            except Exception as e:
                print(f"Error setting phonebook: {e}")

            return message  

        def set_fallalert(self, project: str , switch: bool = True , created : str  | None = None):
            imeis_list = self.get_online_imeis_by_project(project, created)
            message = []
            dbo = db.get_dbo()
            print(f"switch: {switch}")
            try:
                for imei in imeis_list:
                    if switch:
                        response = alert.turn_on(imei.IMEI_id, 8)
                        update_object = {
                            "IMEI_id": imei.IMEI_id,
                            "updated": datetime.now().isoformat()   
                        }
                        dbo.update_object('watches', update_object, "IMEI_id")
                    else:
                        response = alert.turn_off(imei.IMEI_id)
                        update_object = {
                            "IMEI_id": imei.IMEI_id,
                            "updated": datetime.now().isoformat()
                        }
                        dbo.update_object('watches', update_object, "IMEI_id")
                    if response:
                        message.append(f"Fall alert for {imei.IMEI_id} set to {switch}")
                        
                        
                    else:
                        message.append(f"Failed to set fall alert for {imei.IMEI_id}")

            except Exception as e:
                print(f"Error setting fall alert: {e}")

            return message

        def set_power(self , project , reboot :bool = True , created : str | None = None):
            imeis_list = self.get_online_imeis_by_project(project , created)
            message = []
            dbo = db.get_dbo()
            try:
                for imei in imeis_list:
                    if reboot:
                        response = miwi.send_command({
                            "Imei": imei.IMEI_id,
                            "timestamp": timestamp,
                            "CommandCode": "0010",
                            "CommandValue": ""
                        })
                        if response:
                            message.append(f"Power command for {imei.IMEI_id} set to reboot")
                            update_object = {
                                "IMEI_id": imei.IMEI_id,
                                "online_status": 1,
                                'updated': datetime.now().isoformat()
                            }
                            dbo.update_object('watches', update_object, "IMEI_id")
                    else:
                        response = miwi.send_command({
                            "Imei": imei.IMEI_id,
                            "timestamp": timestamp,
                            "CommandCode": "0048",
                            "CommandValue": ""
                        })
                        if response:
                            message.append(f"Power command for {imei.IMEI_id} set to off")
                            update_object = {
                                "IMEI_id": imei.IMEI_id,
                                "online_status": 0,
                                'updated': datetime.now().isoformat()
                            }
                            dbo.update_object('watches', update_object, "IMEI_id")

            except Exception as e:
                print(f"Error setting power command: {e}")

            return message
        
        def set_locate(self , project , created: str | None = None):
            if not project:
                return False
            imeis_list = self.get_online_imeis_by_project(project , created)
            message = []
            dbo = db.get_dbo()
            try:
                for imei in imeis_list:
                    response = miwi.send_command({
                        "Imei": imei.IMEI_id,
                        "CommandCode": "0039",
                        "CommandValue": ""
                    })
                    if response:
                        message.append(f"Locate command for {imei.IMEI_id} sent")
                        update_object = {
                            "IMEI_id": imei.IMEI_id,
                            'updated': datetime.now().isoformat()
                        }
                        dbo.update_object('watches', update_object, "IMEI_id")
                    else:
                        message.append(f"Failed to send locate command for {imei.IMEI_id}")

            except Exception as e:
                print(f"Error setting locate command: {e}")

            return message

    

            
            