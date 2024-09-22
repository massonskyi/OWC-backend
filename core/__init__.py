# for alembic
# from  functions.async_logger import AsyncLogger

# for main server
from functions.async_logger import AsyncLogger
from typing import Optional # noqa: F401

from .config import load_config

__all__ = [
    'cfg',
    'setup'
]
logger = AsyncLogger("config")
cfg = {}

async def init_config():
    """
    Initialize config from config.py
    :param: None
    :return: None
    """
    global cfg
    config = await load_config(logger)  # Ожидаем завершение корутины

    # Получаем значения конфигурации с помощью await
    cfg['DATABASE_URL'] = await config.getattr('DATABASE_URL')
    cfg['BACKEND_SECRET_COOKIE_KEY'] = await config.getattr('BACKEND_SECRET_COOKIE_KEY')

    cfg['POSTGRES_DB'] = await config.getattr('POSTGRES_DB')
    cfg['POSTGRES_USER'] = await config.getattr('POSTGRES_USER')
    cfg['POSTGRES_PASSWORD'] = await config.getattr('POSTGRES_PASSWORD')

    cfg['DB_USER'] = await config.getattr('DB_USER')
    cfg['DB_PASSWORD'] = await config.getattr('DB_PASS')
    cfg['DB_HOST'] = await config.getattr('DB_HOST')
    cfg['DB_PORT'] = await config.getattr('DB_PORT')
    cfg['DB_NAME'] = await config.getattr('DB_NAME')

async def setup():
    await init_config()