from typing import (
    List, 
    Union,
    Tuple
)

from fastapi import (
    APIRouter, 
    FastAPI
)
from starlette.middleware.cors import CORSMiddleware
from typing import Optional # noqa: F401
from pydantic_settings import BaseSettings

from functions.async_logger import AsyncLogger

__all__ = [
    "setup_middleware", 
    "Settings",
    "setup_endpoints"
]

__version__ = "1.0.0"

__doc__ = """
Settings for the Admin Shop API application.
"""


log = AsyncLogger("Settings")

async def setup_middleware(
    app: FastAPI, 
    allow_origins: Union[str, List[str]] = None,
    allow_credentials: bool = False,
    allow_methods: Union[str, List[str]] = None,
    allow_headers: Union[str, List[str]] = None
) -> bool:
    """
    Setup CORS middleware, and add it to the app middleware list.
    :param app: FastAPI app instance to add middleware
    :param CORS: CORS middleware instance to add to app middleware list if needed to enable CORS support
    :param allow_credetials: Allow credentials for CORS support, defaults to False
    :param allow_origins: List of allowed origins for CORS support
    :param allow_methods: List of allowed methods for CORS support
    :param allow_headers: List of allowed headers for CORS support
    :return: True if CORS middleware was successfully added to app middleware list, False otherwise
    """
    
    assert isinstance(app, FastAPI), "app must be an instance of FastAPI"
    
    if not allow_origins:
        allow_origins = ["*"]
        
    if not allow_methods:
        allow_methods = ["*"]
        
    if not allow_headers:
        allow_headers = ["*"]

    try:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,  # Specify allowed origins here
            allow_credentials=allow_credentials,
            allow_methods=allow_methods,  # Allow all methods (GET, POST, etc.)
            allow_headers=allow_headers,  # Allow all headers
        )
    except Exception as e:
        await log.b_err(f"Failed setup middleware: {e}")
        return False
    
    else:
        await log.b_info(f"Successfully setup middleware")
        return True
    
async def setup_endpoints(
    app: FastAPI,
    endpoints: List[Tuple[str, APIRouter]] = None,
) -> bool:
    """
    Setup endpoints for the Admin Shop API application.
    :param app: FastAPI app instance to add endpoints to
    :param endpoints: List of endpoints to add to app
    :return: True if endpoints were successfully added to app, False otherwise
    """
    
    if not endpoints:
        return False
    
    for endpoint in endpoints:
        try:
            app.include_router(
                endpoint[1],
                prefix=endpoint[0]
            )
        except Exception as e:
            await log.b_err(f"Failed to add endpoint: {e}")
            return False
        else:
            await log.b_info(f"Successfully added endpoint: {endpoint[0]}{endpoint[1].prefix}")
    
    return True

class Settings(BaseSettings):
    """
    Settings for the Admin Shop API application.
    """
    application_name: str = "Online Workspace Code For You API (OWC)"
    debug: bool = True
    backend_secret_cookie_key: str
    postgres_db: str
    postgres_user: str
    postgres_password: str
    environment: str
    db_user: str
    db_host: str
    db_port: str
    db_name: str
    db_pass: str
    database_url: str

    class Config:
        """
        Config class for Settings application.
        """
        env_file = ".env"