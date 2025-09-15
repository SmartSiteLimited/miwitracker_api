import mariadb
import pydantic
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_config
from app.core.logger import get_logger
from app.routes import devices, groups, projects, settings
from app.schema.exceptions import AppException
from app.schema.response import ResponsePayload

project_name = get_config("server.project_name", "Miwitracker API")
origins = get_config("server.allow_origins", "*")


@asynccontextmanager
async def lifespan(server: FastAPI):
    # Startup
    get_logger().info(f"Starting {project_name}...")
    yield
    # Shutdown
    get_logger().info(f"{project_name} shutdown complete.")


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except (HTTPException, StarletteHTTPException) as ex:
            if ex.status_code == 404:
                return await super().get_response("index.html", scope)
            else:
                raise ex


server = FastAPI(
    title="Miwitracker API",
    version="1.0.0",
    lifespan=lifespan,
)

server.mount("/webapp", SPAStaticFiles(directory="webapp", html=True), name="webapp")

server.add_middleware(
    CORSMiddleware,
    allow_origins=origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


server.include_router(projects.router)
server.include_router(devices.router)
server.include_router(settings.router)
server.include_router(groups.router)


@server.exception_handler(pydantic.ValidationError)
async def validation_error_handler(request, exc: pydantic.ValidationError):
    get_logger().warning("validation_error_handler", exc)
    error_msg = "Invalid Form Data: \n"
    for error in exc.errors():
        error_msg += f"{error.get('loc', '')}\n"

    resp = ResponsePayload(success=False, message=error_msg)

    return JSONResponse(content=resp.model_dump(), status_code=400)


@server.exception_handler(AppException)
async def app_error_handler(request, exc: AppException):
    get_logger().warning("app_error_handler", exc)
    resp = ResponsePayload(success=False, message=f"An unexpected error occurred: {exc.detail}")

    return JSONResponse(content=resp.model_dump(), status_code=500)


@server.exception_handler(mariadb.DatabaseError)
async def database_error_handler(request, exc: mariadb.DatabaseError):
    get_logger().error("Database Error", exc)
    resp = ResponsePayload(success=False, message="Database error occurred")

    return JSONResponse(content=resp.model_dump(), status_code=500)


@server.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    get_logger().error("general_exception_handler", exc)
    resp = ResponsePayload(success=False, message=f"An unexpected error occurred: {str(exc)}")

    return JSONResponse(content=resp.model_dump(), status_code=500)
