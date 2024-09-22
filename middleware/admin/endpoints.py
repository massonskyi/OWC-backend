from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_async_db
from middleware.admin.manager import AdminManager
from middleware.user.schemas import UserResponseSchema, UserCreateSchema
from typing import Optional # noqa: F401
endpoint = APIRouter(
    prefix="/admin",
    tags=["ADMIN MODULE API"],
)

# Инициализация AdminManager
async def get_admin_manager(
    db: AsyncSession = Depends(get_async_db)
) -> 'AdminManager':
    """
    Get admin manager instance.
    Args:
    :
    :return: Admin manager instance.
    """
    return AdminManager(db=db)

@endpoint.get("/get_users", response_model=List[UserResponseSchema])
async def get_users(admin_manager: AdminManager = Depends(get_admin_manager)):
    """
    Get all users from database.
    :return: HTTP 200 OK response with list of all users in database as JSON format and status code 200.
    """
    try:
        users = await admin_manager.get_all_users()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@endpoint.get("/get_user/{user_id}", response_model=UserResponseSchema)
async def get_user(user_id: int, admin_manager: AdminManager = Depends(get_admin_manager)):
    """
    Get user by ID.
    :param admin_manager: Admin manager object. Used to get user sessions.
    :param user_id: ID of the user to retrieve.
    :return: User object in JSON format.
    """
    try:
        user = await admin_manager.get_user(user_id)
        return user
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@endpoint.post("/create_user", response_model=str)
async def create_user(new_user: UserCreateSchema, admin_manager: AdminManager = Depends(get_admin_manager)):
    """
    Create a new user.
    :param admin_manager: Admin manager object. Used to get user sessions.
    :param new_user: Data for the new user.
    :return: Access token for the newly created user.
    """
    try:
        token = await admin_manager.create_user(new_user)
        return token
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@endpoint.put("/update_user/{user_id}", response_model=UserResponseSchema)
async def update_user(user_id: int, updated_user: UserCreateSchema, admin_manager: AdminManager = Depends(get_admin_manager)):
    """
    Update an existing user.
    :param admin_manager: Admin manager instance. Used to get user sessions.
    :param user_id: ID of the user to update.
    :param updated_user: New data for the user.
    :return: Updated User object in JSON format.
    """
    try:
        user = await admin_manager.update_user(user_id, updated_user)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@endpoint.delete("/delete_user/{user_id}")
async def delete_user(user_id: int, admin_manager: AdminManager = Depends(get_admin_manager)):
    """
    Delete a user by ID.
    :param admin_manager: Admin manager instance. Used to get user sessions.
    :param user_id: ID of the user to delete.
    :return: Success message.
    """
    try:
        await admin_manager.delete_user(user_id)
        return {"detail": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@endpoint.post("/block_user/{user_id}")
async def block_user(user_id: int, admin_manager: AdminManager = Depends(get_admin_manager)):
    """
    Block a user by ID.
    :param admin_manager: Admin manager instance. Used to get user sessions.
    :param user_id: ID of the user to block.
    :return: Success message.
    """
    try:
        await admin_manager.block_user(user_id)
        return {"detail": "User blocked successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@endpoint.post("/unblock_user/{user_id}")
async def unblock_user(user_id: int, admin_manager: AdminManager = Depends(get_admin_manager)):
    """
    Unblock a user by ID.
    :param admin_manager: Admin manager instance. Used to get user sessions.
    :param user_id: ID of the user to unblock.
    :return: Success message.
    """
    try:
        await admin_manager.unblock_user(user_id)
        return {"detail": "User unblocked successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@endpoint.get("/get_user_sessions/{user_id}")
async def get_user_sessions(user_id: int, admin_manager: AdminManager = Depends(get_admin_manager)):
    """
    Get all active sessions of a user.
    :param admin_manager: AdminManager object. Used to get user sessions.
    :param user_id: ID of the user.
    :return: List of active sessions.
    """
    try:
        sessions = await admin_manager.get_user_sessions(user_id)
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
