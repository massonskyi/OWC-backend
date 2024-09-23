import base64
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.user.models import User
from middleware.profile.manager import ProfileManager
from database.session import get_async_db
from middleware.user.schemas import UserResponseSchema, UserCreateSchema
from middleware.utils import get_current_user
from typing import Optional # noqa: F401

endpoint = APIRouter(
    prefix="/profile",
    tags=["profile"],
)

# Инициализация ProfileManager
async def get_profile_manager(
    db: AsyncSession = Depends(get_async_db)
) -> 'ProfileManager':
    """
    Get profile manager instance. 
    Args:
        db: Database connection. Used to get database connection.
    
    Returns:
        ProfileManager instance. Used to get user profile.
        
    Raises:
        HTTPException: If user is not authenticated.
    """
    return ProfileManager(db=db)

# Пример функции для получения изображения
def get_user_avatar(avatar_path: str) -> str:
    try:
        with open(avatar_path, "rb") as image_file:
            image_data = image_file.read()
        return base64.b64encode(image_data).decode('utf-8')
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Avatar not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving the avatar: {e}")

@endpoint.get(
    "/{user_id}", 
    response_model=UserResponseSchema,
    summary="Get user profile by ID.",
)
async def get_user_profile(
    user_id: int, 
    profile_manager: ProfileManager = Depends(get_profile_manager),
    current_user: User = Depends(get_current_user)
) -> UserResponseSchema:
    """
    Get user profile by ID.
    :param profile_manager: Profile manager object. Used to get user profile.
    :param user_id: ID of the user to retrieve.
    :return: User profile object in JSON format.
    """"""  """
    try:
        user_profile = await profile_manager.get_user_profile(user_id)
        avatar_data = get_user_avatar(user_profile.avatar)
        user_data = user_profile.dict()
        user_data['avatar'] = avatar_data
        return user_data
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@endpoint.put(
    "/{user_id}", 
    response_model=UserResponseSchema,
    summary="Update user profile by ID.",
)
async def update_user_profile(
    user_id: int, 
    updated_user: UserCreateSchema, 
    profile_manager: ProfileManager = Depends(get_profile_manager),
    current_user: User = Depends(get_current_user)
)->UserResponseSchema:
    """
    Update an existing user profile.
    :param profile_manager: Profile manager instance. Used to update user profile.
    :param user_id: ID of the user to update.
    :param updated_user: New data for the user profile.
    :return: Updated User profile object in JSON format.
    """
    try:
        user_profile = await profile_manager.update_user_profile(user_id, updated_user)
        return user_profile
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@endpoint.delete(
    "/{user_id}",
    summary="Delete user profile by ID.",
)
async def delete_user_profile(
    user_id: int, 
    profile_manager: ProfileManager = Depends(get_profile_manager),
    current_user: User = Depends(get_current_user)    
) -> JSONResponse:
    """
    Delete a user profile by ID.
    :param profile_manager: Profile manager instance. Used to delete user profile.
    :param user_id: ID of the user to delete.
    :return: Success message.
    """
    try:
        await profile_manager.delete_user_profile(user_id)
        return {"detail": "User profile deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
