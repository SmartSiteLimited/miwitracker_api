import pydantic
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_config
from app.routes import devices, projects , settings
from app.schema.exceptions import AppException
from app.schema.response import ResponsePayload

# from .dependencies import get_query_token, get_token_header
# from .internal import admin
# from .routers import items, users

project_name = get_config('server.project_name', 'Smartsite DWSS API')
origins = get_config('server.allow_origins', '*')


@asynccontextmanager
async def lifespan(server: FastAPI):
    # Startup
    print("Starting up...")
    yield
    # Shutdown
    print("Shutting down...")
    # await dbo.dispose()


server = FastAPI(
    title="Miwitracker API",
    version="1.0.0",
    lifespan=lifespan,
)

server.add_middleware(
    CORSMiddleware,
    allow_origins=origins.split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


server.include_router(projects.router)
server.include_router(devices.router)
server.include_router(settings.router)

@server.exception_handler(pydantic.ValidationError)
async def validation_error_handler(request, exc: pydantic.ValidationError):
    print("validation_error_handler", exc)
    error_msg = "Invalid Form Data: \n"
    for error in exc.errors():
        error_msg += f"{error.get('loc', '')}\n"

    resp = ResponsePayload(success=False, message=error_msg)

    return JSONResponse(content=resp.model_dump(), status_code=400)


@server.exception_handler(AppException)
async def app_error_handler(request, exc: AppException):
    resp = ResponsePayload(success=False, message=f"An unexpected error occurred: {exc.detail}")

    return JSONResponse(content=resp.model_dump(), status_code=500)


@server.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    print("general_exception_handler", exc)
    resp = ResponsePayload(success=False, message=f"An unexpected error occurred: {str(exc)}")

    return JSONResponse(content=resp.model_dump(), status_code=500)
