from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional # noqa: F401
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get AsyncSession object from database connection
    :params: None
    :yields: AsyncSession object from database connection
    """
    from database.connection import AsyncSessionLocal, init_db

    if AsyncSessionLocal is None:  # If AsyncSessionLocal is None, initialize the DB
        await init_db()
    async with AsyncSessionLocal() as session:
        yield session