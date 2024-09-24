import argparse
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from functions.async_logger import AsyncLogger
from core import setup
from database.connection import init_db

from core.settings import Settings, setup_endpoints
from middleware.user.endpoints import API_USER_MODULE
from middleware.admin.endpoints import endpoint as ADMIN_ENDPOINTS
from middleware.profile.endpoints import endpoint as PROFILE_ENDPOINTS
from middleware.search.endpoints import API_SEARCH_MODULE
from typing import Optional # noqa: F401

settings = Settings()
logger = AsyncLogger(__name__)

BUILD_DIRECTORY: Optional[str] = f'{os.getcwd()}/static/static/'
SOURCE_DIRECTORY: Optional[str] = f'{os.getcwd()}/static/'
INDEX_DIRECTORY: Optional[str] = f'{os.getcwd()}/static/index.html'

@asynccontextmanager
async def lifespan_context(app: FastAPI):
    await setup() 
    await logger.b_info(f"{settings.application_name} is running")
    await init_db()
    from core import cfg
    await logger.b_info(f"{settings.application_name} is conneting to database {cfg['DATABASE_URL']}")
    await initial_server()
    await logger.b_info(f"{settings.application_name} is starting")
    
    yield

app = FastAPI(
    title=settings.application_name,
    debug=settings.debug,
    lifespan=lifespan_context
)
# Укажите путь к собранной папке вашего React приложения
app.mount("/static", StaticFiles(directory=BUILD_DIRECTORY), name="static")

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://10.78.1.48:3000",  # Add your React app's origin here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specify allowed origins here
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)
endpoints = []
async def initial_server():

    global endpoints
        
    endpoints.append(("/api_version_1", API_USER_MODULE))
    endpoints.append(("/api_version_1", ADMIN_ENDPOINTS ))
    endpoints.append(("/api_version_1", PROFILE_ENDPOINTS))
    endpoints.append(("/api_version_1", API_SEARCH_MODULE))
    await setup_endpoints(
        app=app,
        endpoints=endpoints
    )
@app.get(
    "/",
    summary="Home page",
)
async def index():
    return HTMLResponse(
        open(INDEX_DIRECTORY).read()
    )
    
@app.get(
    "/static/{file_path:path}",
    summary="Get static files",
)
async def static(file_path: str):
    return StaticFiles(directory=SOURCE_DIRECTORY)(file_path)

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )
# @app.get("/{full_path:path}")
# async def catch_all(full_path: str):
#     # Возвращаем index.html для любых запросов, которые не соответствуют API
#     with open(INDEX_DIRECTORY, 'r') as file:
#         return HTMLResponse(content=file.read(), status_code=200)
    
def create_parser() -> argparse.ArgumentParser:
    """
    Create argument parser for CLI
    """
    parser = argparse.ArgumentParser(description="Запуск сервера")
    parser.add_argument("--host", default="127.0.0.1", type=str)
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--reload", default=False, type=bool)
    return parser

if __name__ == "__main__":
    """
    If u start server from console
    """
    import uvicorn
    parser = create_parser()
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)
