from datetime import datetime
import os
from fastapi import FastAPI, Form, HTTPException
from typing import Generic, TypeVar , Optional
from fastapi.datastructures import FormData
from pydantic import BaseModel
import uvicorn
from app.models.watch import WatchItems
from app.models.settings import Settings
import miwi 
from fastapi.middleware.cors import CORSMiddleware
RT = TypeVar("RT")

class ResponsePayload(BaseModel, Generic[RT]):
    success: bool
    data: RT | None = None
    message: str | None = None

from configparser import ConfigParser
config = ConfigParser()
config.read("config.ini")

app = FastAPI(
    title="miwi API",
    version="1.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post('/fetch_watches')
def fetch_watches():
    try:
        models = WatchItems()
        result = models.fetch_watches_from_api()
        return ResponsePayload[RT](success=True, message="Watches fetched successfully", data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get('/get_projects')
def get_projects():
    try:
        models = WatchItems()
        result = models.get_project_list()
        if not result:
            return ResponsePayload[RT](success=False, message="No projects found", data=[])
        return ResponsePayload[RT](success=True, message="Projects fetched successfully", data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/get_imeis_by_project')
def get_imeis_by_project(project: str = Form(...), created: str = Form(None)):
    try:
        models = WatchItems()
        result = models.get_watches_by_project(project, created)
        if not result:
            return ResponsePayload[RT](success=False, message="No watches found for this project", data=[])
        return ResponsePayload[RT](success=True, message="Watches fetched successfully", data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/set_sos")
def set_sos(project: str = Form(...) , created: Optional[str] = Form(None), settings: list[str] | None = Form(None) , imeis: list[str] | None = Form(None)):
    try:
        models = WatchItems()
        result = models.set_sos(project, created, settings, imeis)
        return ResponsePayload[RT](success=True, message="SOS commands sent successfully", data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/set_phone_book")
def set_phone_book(project: str = Form(...) , created: Optional[str] = Form(None), settings: list[str] | None = Form(None) , imeis: list[str] | None = Form(None)):
    try:
        models = WatchItems()
        result = models.set_phonebook(project , created , settings , imeis)
        return ResponsePayload[RT](success=True, message="Phone book commands sent successfully", data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@app.post("/check_online")


def check_online(project: str = Form(...), created: Optional[str] = Form(None) , imeis: list[str] | None = Form(None)):
    try:
        models = WatchItems()
        message = models.check_online_by_api(project , created , imeis)
        return ResponsePayload[RT](success=True, message="Online status checked successfully", data=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/set_block_phone")
def set_block_phone(project: str = Form(...), switch: str = Form(...), created: Optional[str] = Form(None) , imeis: list[str] | None = Form(None)):
    try:
        models = WatchItems()
        if switch == '1':
            flag = True
        elif switch == '0':
            flag = False
        result = models.set_block_phone(project, flag , created , imeis)
        return ResponsePayload[RT](success=True, message="Block phone commands sent successfully", data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/set_health')
def set_health(project: str = Form(...), created: Optional[str] = Form(None) , imeis: list[str] | None = Form(None)):
    try:
        models = WatchItems()        
        result = models.set_health(project , created , imeis)
        return ResponsePayload[RT](success=True, message="Health commands sent successfully", data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post('/set_callcenter')
def set_callcenter(project: str = Form(...), created: Optional[str] = Form(None) , settings: list[str] | None = Form(None) , imeis: list[str] | None = Form(None)):
    try:
        models = WatchItems()
        result = models.set_callcenter(project, created, settings, imeis)
        return ResponsePayload[RT](success=True, message="Call center commands sent successfully", data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post('/set_alert')
def set_alert(project: str = Form(...) , switch: bool = True , created: Optional[str] = Form(None) , imeis: list[str] | None = Form(None)):
    try:
        models = WatchItems()
        result = models.set_fallalert(project , switch , created , imeis)
        return ResponsePayload[RT](success=True, message="Alert commands sent successfully", data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
@app.post('/locate')
def locate(project: str = Form(...) , created: Optional[str] = Form(None) , imeis: list[str] | None = Form(None)):
    try:
        models = WatchItems()
        result = models.set_locate(project, created, imeis)
        return ResponsePayload[RT](success=True, message="Locate commands sent successfully", data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/power')
def poweroff(project: str = Form(...) , switch: str = Form(...) , created: Optional[str] = Form(None) , imeis: list[str] | None = Form(None)):
    
    try:
        models = WatchItems()
        if switch == '1':
            flag = True
        elif switch == '0':
            flag = False
        result = models.set_power(project, flag , created , imeis)
        return ResponsePayload[RT](success=True, message="Power off commands sent successfully", data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/get_setting_by_project')
def get_setting_by_project(project: str = Form(...)):
    try:
        models = Settings()
        result = models.get_setting_by_projects(project)
        if not result:
            return ResponsePayload[RT](success=False, message="No settings found for this project", data=None)
        return ResponsePayload[RT](success=True, message="Settings fetched successfully", data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
if __name__ == '__main__':
    uvicorn.run(app, host='localhost', port=8000)