# New endpoint to search users
from fastapi import (
    Depends,
    HTTPException,
    APIRouter
)
from fastapi.responses import JSONResponse
from sqlalchemy import select

from database.session import get_async_db
from middleware.user.models import User
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Optional # noqa: F401
API_SEARCH_MODULE = APIRouter(
    prefix="/search",
    tags=['API MODULE SEARCH']
)
@API_SEARCH_MODULE.get(
    "/",
    summary="Search users. TODO: projects, workspaces"
)
async def search_users(
    query: str, 
    db: AsyncSession = Depends(get_async_db)
)->JSONResponse:
    """
    Search users, projects, workspaces
    Args:
        query: str, search query by username or email or full name
        db: database connection
    Returns:
        JSONResponse: JSONResponse object  with users list

    """
    
    # TODO: Добавить поиск проектов и воркспейсов после их интеграции
    try:
        result = await db.execute(
            select(User).filter(
                (User.username.ilike(f"%{query}%")) |
                (User.email.ilike(f"%{query}%"))
            ).distinct()  # Добавьте distinct(), чтобы избежать дубликатов
        )

        users = result.scalars().all()
        users_list = [user.to_dict() for user in users]
        return JSONResponse(content={"users": users_list})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))