from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from middleware.utils import PasswordManager
from middleware.user.schemas import UserResponseSchema, UserCreateSchema
from middleware.user.models import User

from functions.async_logger import AsyncLogger
from typing import Optional # noqa: F401


class ProfileManager:
    """
    Profile manager class. This class manages the user profile database.
    The manager class is responsible for managing the user profile database.
    """

    logger = AsyncLogger(__name__)
    password_manager = PasswordManager()

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_profile(self, user_id: int) -> UserResponseSchema:
        """
        Retrieve a user profile by their ID.

        Args:
            user_id: The ID of the user to retrieve.

        Returns:
            The UserResponseSchema object.

        Raises:
            Exception: If the user does not exist.
        """
        await self.logger.b_info(f"Retrieving user profile with ID: {user_id}")
        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if not user:
            await self.logger.b_exc(f"User with ID: {user_id} not found")
            raise Exception(f"User with ID: {user_id} not found")
        return UserResponseSchema(**user.__dict__)
    
    async def update_user_profile(self, user_id: int, new: UserCreateSchema) -> UserResponseSchema:
        """
        Update the user profile with the given ID with the new data.

        Args:
            user_id: The ID of the user to update.
            new: A UserCreateSchema object containing the new user data.

        Returns:
            The updated UserResponseSchema object.

        Raises:
            ValueError: If the input data is invalid or the email is already in use by another user.
            Exception: If an error occurs during database operation.
        """
        await self.logger.b_info(f"Updating user profile with ID: {user_id}")

        # Check if the new email is already in use by another user
        if new.email:
            result = await self.db.execute(select(User).filter(User.email == new.email, User.id != user_id))
            existing_user = result.scalars().first()
            if existing_user:
                await self.logger.b_exc(f"Email {new.email} is already in use by another user")
                raise ValueError(f"Email {new.email} is already in use by another user")

        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if not user:
            await self.logger.b_exc(f"User with ID: {user_id} not found")
            raise Exception(f"User with ID: {user_id} not found")

        for key, value in new.dict().items():
            if key == 'hash_password':
                value = self.password_manager.hash(value)
            setattr(user, key, value)

        try:
            await self.db.commit()
            await self.db.refresh(user)
            await self.logger.b_info(f"User profile with ID: {user_id} updated successfully")
            return UserResponseSchema(**user.__dict__)
        except Exception as e:
            await self.db.rollback()
            await self.logger.b_err(f"Error updating user profile: {e}")
            raise e

    async def delete_user_profile(self, user_id: int) -> None:
        """
        Delete the user profile with the given ID.

        Args:
            user_id: The ID of the user to delete.

        Raises:
            Exception: If an error occurs during database operation.
        """
        await self.logger.b_info(f"Deleting user profile with ID: {user_id}")
        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if user:
            await self.db.delete(user)
            try:
                await self.db.commit()
                await self.logger.b_info(f"User profile with ID: {user_id} deleted successfully")
            except Exception as e:
                await self.db.rollback()
                await self.logger.b_err(f"Error deleting user profile: {e}")
                raise e
        else:
            await self.logger.b_exc(f"User with ID: {user_id} not found")