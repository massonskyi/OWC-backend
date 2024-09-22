from typing import List
from typing import Optional # noqa: F401
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from middleware.utils import PasswordManager
from middleware.user.schemas import UserCreateSchema, UserResponseSchema
from middleware.user.models import User, UserToken
from middleware.user.manager import UserManager

from functions.async_logger import AsyncLogger


class AdminManager:
    """
    Admin manager class. This class manages the user database.
    The manager class is responsible for managing the user database.
    """

    password_manager = PasswordManager()
    logger = AsyncLogger(__name__)

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_manager = UserManager(db=db)

    async def create_user(self, new: UserCreateSchema) -> str:
        """
        Create a new user with the given data.

        Args:
            new: A UserCreateSchema object containing the user data.

        Returns:
            The access token for the newly created User object.

        Raises:
            ValueError: If the input data is invalid.
            Exception: If an error occurs during database operation.
        """
        await self.logger.b_info("Creating new user, retranslated to user manager")
        return await self.user_manager.create_user(new)

    async def delete_user(self, user_id: int) -> None:
        """
        Delete the user with the given ID.

        Args:
            user_id: The ID of the user to delete.

        Raises:
            Exception: If an error occurs during database operation.
        """
        await self.logger.b_info(f"Deleting user with ID: {user_id}")
        return await self.user_manager.delete_user(user_id)

    async def update_user(self, user_id: int, new: UserCreateSchema) -> User:
        """
        Update the user with the given ID with the new data.

        Args:
            user_id: The ID of the user to update.
            new: A UserCreateSchema object containing the new user data.

        Returns:
            The updated User object.

        Raises:
            ValueError: If the input data is invalid.
            Exception: If an error occurs during database operation.
        """
        await self.logger.b_info("Deleted new user, retranslated to user manager")
        return await self.user_manager.update_user(user_id, new)

    async def get_all_users(self) -> List[UserResponseSchema]:
        """
        Retrieve all users from the database.

        Returns:
            A list of UserResponseSchema objects.
        """
        await self.logger.b_info("Retrieving all users")
        result = await self.db.execute(select(User))
        users = result.scalars().all()
        return [UserResponseSchema(**user.__dict__) for user in users]

    async def get_user(self, user_id: int) -> UserResponseSchema:
        """
        Retrieve a user by their ID.

        Args:
            user_id: The ID of the user to retrieve.

        Returns:
            The UserResponseSchema object.

        Raises:
            Exception: If the user does not exist.
        """
        await self.logger.b_info(f"Retrieving user with ID: {user_id}")
        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if not user:
            await self.logger.b_exc(f"User with ID: {user_id} not found")
            raise Exception(f"User with ID: {user_id} not found")
        return UserResponseSchema(**user.__dict__)

    async def block_user(self, user_id: int) -> None:
        """
        Block the user with the given ID.

        Args:
            user_id: The ID of the user to block.

        Raises:
            Exception: If an error occurs during database operation.
        """
        await self.logger.b_info(f"Blocking user with ID: {user_id}")
        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if user:
            user.is_blocked = True
            try:
                await self.db.commit()
                await self.logger.b_info(f"User with ID: {user_id} blocked successfully")
            except Exception as e:
                await self.db.rollback()
                await self.logger.b_err(f"Error blocking user: {e}")
                raise e
        else:
            await self.logger.b_exc(f"User with ID: {user_id} not found")

    async def unblock_user(self, user_id: int) -> None:
        """
        Unblock the user with the given ID.

        Args:
            user_id: The ID of the user to unblock.

        Raises:
            Exception: If an error occurs during database operation.
        """
        await self.logger.b_info(f"Unblocking user with ID: {user_id}")
        result = await self.db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if user:
            user.is_blocked = False
            try:
                await self.db.commit()
                await self.logger.b_info(f"User with ID: {user_id} unblocked successfully")
            except Exception as e:
                await self.db.rollback()
                await self.logger.b_error(f"Error unblocking user: {e}")
                raise e
        else:
            await self.logger.b_warn(f"User with ID: {user_id} not found")

    async def get_user_sessions(self, user_id: int) -> List[UserToken]:
        """
        Get all active sessions of the user.

        Args:
            user_id: The ID of the user.

        Returns:
            A list of UserToken objects representing active sessions.
        """
        await self.logger.b_info(f"Getting sessions for user with ID: {user_id}")
        result = await self.db.execute(select(UserToken).filter(UserToken.user_id == user_id))
        sessions = result.scalars().all()
        return sessions
