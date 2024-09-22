from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

from core import cfg
from typing import Optional # noqa: F401
async_engine = None
AsyncSessionLocal = None
Base = declarative_base()
metadata = MetaData()
async def init_db():
    global async_engine, AsyncSessionLocal

    if async_engine is None:
        try:
            # Create async engine
            async_engine = create_async_engine(cfg["DATABASE_URL"], echo=True)

            # Create session factory
            AsyncSessionLocal = sessionmaker(
                bind=async_engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )

        except SQLAlchemyError as e:
            raise

    if AsyncSessionLocal is None:
        raise RuntimeError("AsyncSessionLocal was not properly initialized")