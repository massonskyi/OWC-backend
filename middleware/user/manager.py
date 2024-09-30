import datetime
import shutil
import uuid
import docker
from typing import List, Tuple, Union, Any
from typing import Optional
from typing_extensions import deprecated # noqa: F401
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError


from core.const import DEFAULT_USER_AVATAR_PATH


from middleware.utils import PasswordManager, create_access_token
from middleware.user.schemas import  UserCreateSchema, WorkspaceSchema, WorkspaceResponseSchema, Token
from middleware.user.models import  User, UserToken
import os
import subprocess
from contextlib import contextmanager
from typing import Any
from sqlalchemy import select, update
from core import cfg
from functions.async_logger import AsyncLogger
from sqlalchemy.ext.asyncio import AsyncSession
from middleware.user.models import Workspace

__all__ = [
    'UserManager'
]

class UserManager:
    """
    User manager class. This class manages the user database. 
    The manager class is responsible for managing the user database.
    
    """
    logger = AsyncLogger(__name__)
    USING_LANGUAGE = ['python', 'c', 'cpp', 'js', 'cs', 'ruby', 'go']

    def __init__(
        self, 
        db: AsyncSession
    ) -> None:
        """
        Initialization method. This method initializes the user manager.
        """
        
        self.password_manager = PasswordManager()
        self.__async_db_session = db
        
        
    async def create_user(
        self, 
        new: UserCreateSchema,
    ) -> Tuple[UserCreateSchema, str, str]:
        """
        Create a new user. This method creates a new user. 
        Args:
            new: A UserCreateSchema object containing the new user data.
        Returns:
            UserCreateSchema object containing the new user data.
            If an error occurs during database operation.
        Raises: 
            ValueError: If the input data is invalid.
        """
        if not new.validate():
            await self.logger.b_crit(f"Invalid input data")
            raise ValueError("Invalid input data")

        hashed_password = self.password_manager.hash(new.hash_password)
        
        # Create user instance with initial tokens as empty strings
        new_user = User(
            name=new.name,
            surname=new.surname,
            email=new.email,
            phone=new.phone,
            age=new.age,
            username=new.username,
            hash_password=hashed_password,
            avatar='',
            token='',  # Initialize with empty token
            refresh_token=''  # Initialize with empty refresh token
        )
        if new.avatar:
            avatar_filename: str = f"avatar_{new.username}_{new.avatar.filename}"
            avatar_path = f"static/static/uploads/{avatar_filename}"
            
            #save
            with open(avatar_path, "wb") as buffer:
                shutil.copyfileobj(new.avatar.file, buffer)
            
            new_user.avatar = avatar_path
        else:
            new_user.avatar = DEFAULT_USER_AVATAR_PATH
            

        
        try:
            # Add the new user to the databasez
            async with self.__async_db_session as async_session:
                async with async_session.begin():
                    async_session.add(new_user)
                    await async_session.commit()  # Commit to persist user and obtain user ID

            # Retrieve the newly created user
            async with self.__async_db_session as async_session:
                user = await async_session.execute(select(User).filter(User.email == new_user.email))
                user = user.scalars().first()

            # Create workspace and projects for the user
            workspace = user.create_workspace()
            if not workspace:
                await self.logger.b_crit(f"Failed to create workspaces, workspace = {workspace}")
                raise ValueError("Failed to create workspaces, workspace = {workspace}")

            # Add the workspace and projects to the database
            async with self.__async_db_session as async_session:
                async with async_session.begin():
                    async_session.add(workspace)
                    await async_session.commit()  # Commit to persist and projects

            async with self.__async_db_session as async_session:
                workspace = await async_session.execute(select(Workspace).filter(Workspace.user_id == user.id))
                workspace = workspace.scalars().first()
        except Exception as e:
            await self.logger.b_crit(f"Failed to create workspaces: {e}")
            raise ValueError(f"Failed to create workspaces: {e}")
        
        try:
            # Create access token and refresh token
            access_token, expire = create_access_token(
                data={"sub": str(user.id)},
            )
            
            if access_token is None or access_token == '':
                await self.logger.b_crit(f"Failed to generate access token, token is empty")
                raise ValueError("Failed to generate access token")
        
        except Exception as e:
            raise Exception(f"failed to create access_token = {e} {user.id}")
        
        try:
            db_token = UserToken(
                token=access_token,
                expiration=expire,
                user_id=user.id
            )
            async with self.__async_db_session as async_session:
                async with async_session.begin():
                    async_session.add(db_token)
                    await async_session.commit()
            user.token = access_token
            user.refresh_token = access_token  # Assuming same token for simplicity
            
            # Re-open session to update user with new tokens
            async with self.__async_db_session as async_session:
                async with async_session.begin():
                    async_session.add(user)
                    await async_session.commit()  # Commit to update user with tokens
                    
            await self.logger.b_info(f"User created with access_token = {access_token}")
            return user, access_token, expire

        except SQLAlchemyError as e:
            await self.logger.b_crit(f"SQLAlchemyError: {e}")
            raise HTTPException(status_code=500, detail=f"Error creating user: {e}")
        except Exception as e:
            await self.logger.b_crit(f"Exception: {e}")
            raise HTTPException(status_code=500, detail=f"Error creating user: {e}")


    async def delete_user(
        self, 
        user_id: int
    ) -> None:
        """
        Delete the user with the given ID.

        Args:
            user_id: The ID of the user to delete.

        Raises:
            Exception: If an error occurs during database operation.
        """

        async with self.__async_db_session as session:
            user = await session.execute(select(User).filter(User.id == user_id))
            user = user.scalars().first()
            if user:
                try:
                    await session.delete(user)
                    await session.commit()
                except SQLAlchemyError as e:
                    await self.logger.b_crit(f"SQLAlchemyError: {e}")
                    await session.rollback()
                    raise e
                else:
                    await self.logger.b_info("Successfully deleted user {user_id}")
            else:
                await self.logger.b_crit("User with ID {user_id} not found")
                pass

    async def update_user(
        self, 
        user_id: int, 
        new: UserCreateSchema
    ) -> UserCreateSchema:
        """
        Update the user with the given ID with the new data.

        Args:
            user_id: The ID of the user to update.
            user_dto: A UserDTO object containing the new user data.

        Returns:
            The updated User object.

        Raises:
            ValueError: If the input data is invalid.
            Exception: If an error occurs during database operation.
        """
        if not new.validate():
                raise ValueError("Invalid input data")

        async with self.__async_db_session as session:
            user = await session.execute(select(User).filter(User.id == user_id))
            user = user.scalars().first()
            if user:
                if new.first_name:
                    user.first_name = new.first_name
                if new.last_name:
                    user.last_name = new.last_name
                if new.middle_name:
                    user.middle_name = new.middle_name
                if new.position:
                    user.position = new.position
                if new.username:
                    user.username = new.username
                if new.hash_password:
                    user.hash_password = self.password_manager.hash(new.hash_password)
                try:
                    await session.commit()
                    await session.refresh(user)
                except SQLAlchemyError as e:
                    await self.logger.b_crit("SQL ERROR: {e}")
                    await session.rollback()
                    raise e
                else:
                    await self.logger.b_info("Successfully updated user with ID {user_id}")
            else:
                # User not found, handle accordingly
                await self.logger.b_crit("User with ID {user_id} not found")
                pass


            return UserCreateSchema(**user.to_dict())


    async def authenticate_user(
        self, 
        username: str, 
        password: str
    ) -> tuple[User | None, Any, Any] | tuple[None, None, None]:
        """
        Authenticate a user by checking the email and password against the data in the database.

        Args:
            email: The user's email.
            password: The user's password.

        Returns:
            The authenticated user object if the email and password are valid, or None otherwise.
        """

        async def get_token_by_user_id(
            user_id: int
        ) -> UserToken:
            """
            Get a user's token by their ID from the database.

            Args:
                user_id: The user's ID.

            Returns:
                The user's token if found, or None otherwise.
            """
            async with self.__async_db_session as session:
                token_expire = await session.execute(select(UserToken).filter(UserToken.user_id == user_id))
                token_expire = token_expire.scalars().first()
                return token_expire if token_expire else None

        async with self.__async_db_session as session:
            user = await session.execute(select(User).filter(User.username == username))
            await self.logger.b_info(user)
            user = user.scalars().first()
            if user and self.password_manager.verify(user.hash_password, password):
                token_expire = await get_token_by_user_id(user.id)
                return user, token_expire.token, token_expire.expiration
            return None, None, None
        
    async def generate_new_token(
        self, 
        user_id: int
    ) -> tuple[str, float]:
        """
        Generate a new access token for the user and update the token in the database.

        Args:
            user_id: The user's ID.

        Returns:
            The new token and its expiration timestamp.
        """
        async with self.__async_db_session as session:
            # Генерация нового токена
            new_token = self.token_manager.create_token(user_id=user_id)
            expire_at = (datetime.now() + datetime.timedelta(hours=1)).timestamp()
            
            # Обновление токена в базе данных
            await session.execute(
                update(UserToken).where(UserToken.user_id == user_id).values(token=new_token, expiration=expire_at)
            )
            await session.commit()
            return new_token, expire_at
        
    async def create_workspace(
            self,
            user: User = None,
            new: WorkspaceSchema = None,
    ) -> WorkspaceResponseSchema:
        """
        Creates a new workspace.
        Args:
            user_id (int): ID of the user who owns the workspace.
            new (WorkspaceCreate): The workspace to be created.
        Returns:
            WorkspaceCreate: The created workspace.
        Raises:
            ValueError: If the workspace creation fails.
        """
        new_workspace = Workspace(
            name=new.name,
            user_id=user.id,
            description=new.description,
            is_active=new.is_active,
            is_public=new.is_public,
        )
        new_workspace.create_workspace(user)
        try:
            # Add the new workspace to the database
            async with self.__async_db_session as async_session:
                if not async_session.in_transaction():
                    async with async_session.begin():
                        async_session.add(new_workspace)
                        await async_session.commit()
                else:
                    async_session.add(new_workspace)
                    await async_session.commit()
                
        except SQLAlchemyError as e:
            await self.logger.b_crit(f"SQLAlchemyError: {e}")
            raise ValueError(f"Error creating workspace: {new}")
        
        except Exception as e:
            await self.logger.b_crit(f"Error creating workspace: {new}")
            raise ValueError(f"Error creating workspace: {new}")
        
        return WorkspaceResponseSchema(
            user_id=user.id, name=new_workspace.name, description=new_workspace.description, is_active=new_workspace.is_active, is_public=new_workspace.is_public,files=None
        )
    
    async def update_workspace(
            self,
            user_id: int,
            workspace_id: int,
            updated_data: WorkspaceSchema
    ) -> WorkspaceResponseSchema:
        """
        Updates an existing workspace.
        Args:
            user_id (int): ID of the user who owns the workspace.
            workspace_id (int): The ID of the workspace to update.
            updated_data (WorkspaceSchema): The updated workspace data.
        Returns:
            WorkspaceResponseSchema: The updated workspace.
        Raises:
            ValueError: If the workspace does not exist or the update fails.
        """
        try:
            async with self.__async_db_session as async_session:
                db_workspace = await async_session.execute(
                    select(Workspace)
                    .where(Workspace.id == workspace_id, Workspace.user_id == user_id)
                )
                db_workspace = db_workspace.scalars().first()

                if db_workspace is None:
                    await self.logger.b_crit(f"Workspace not found: {workspace_id}")
                    raise ValueError(f"Workspace not found: {workspace_id}")

                # Обновляем данные рабочей области
                db_workspace.name = updated_data.name
                db_workspace.description = updated_data.description
                db_workspace.is_active = updated_data.is_active
                db_workspace.is_public = updated_data.is_public

                async with async_session.begin():
                    await async_session.commit()

                return WorkspaceResponseSchema(**db_workspace.to_dict())

        except SQLAlchemyError as e:
            await self.logger.b_crit(f"SQLAlchemyError: {e}")
            raise ValueError(f"Error updating workspace: {workspace_id}")

        except Exception as e:
            await self.logger.b_crit(f"Error updating workspace: {workspace_id}")
            raise ValueError(f"Error updating workspace: {workspace_id}") from e
        
    async def get_last_workspace(
            self,
            user_id: int
    ) -> Workspace:
        """
        Get the last workspace created by the user.

        Args:
            user_id (int): The ID of the user who owns the workspace.

        Returns:
            WorkspaceCreateScheme: The last workspace created by the user.

        Raises:
            ValueError: If the workspace does not exist.
        """
        try:
            async with self.__async_db_session as async_session:
                db_workspace = await async_session.execute(
                    select(Workspace)
                    .where(Workspace.user_id == user_id)
                    .order_by(Workspace.created_at.desc())
                    .limit(1)
                )
                db_workspace = db_workspace.scalars().first()

                if db_workspace is None:
                    await self.logger.b_crit(f"No workspaces found for user: {user_id}")
                    raise ValueError(f"No workspaces found for user: {user_id}")

                return db_workspace

        except Exception as e:
            await self.logger.b_crit(f"Error retrieving last workspace for user: {user_id}")
            raise ValueError(f"Error retrieving last workspace for user: {user_id}") from e

    async def get_workspace(
            self,
            user_id: int,
            workspace_id: int
    ) -> WorkspaceResponseSchema:
        """
        Gets a workspace by its ID.
        Args:
            user_id (int): ID of the user who owns the workspace.
            workspace_id (int): The ID of the workspace to retrieve.
        Returns:
            Workspace: The retrieved workspace.
        Raises:
            ValueError: If the workspace does not exist.
        """
        try:
            async with self.__async_db_session as async_session:
                db_workspace = await async_session.execute(
                    select(Workspace)
                    .where(Workspace.id == workspace_id, Workspace.user_id == user_id)
                )
                db_workspace = db_workspace.scalars().first()

                if db_workspace is None:
                    await self.logger.b_crit(f"Workspace not found: {workspace_id}")
                    raise ValueError(f"Workspace not found: {workspace_id}")

                return WorkspaceResponseSchema(**db_workspace.to_dict())

        except Exception as e:
            await self.logger.b_crit(f"Error retrieving workspace: {workspace_id}")
            raise ValueError(f"Error retrieving workspace: {workspace_id}") from e
    @deprecated("You dont need you this method anymore")
    async def get_workspace(self, name: str = None, id: int = None) -> Workspace:
        """
        Get workspace model
        """
        if name:
             async with self.__async_db_session as async_session:
                db_workspace = await async_session.execute(
                    select(Workspace).filter(Workspace.name == name)
                )
                workspace = db_workspace.scalars().first()

                if not workspace:
                    await self.logger.b_info(f"Workspace not found: {name}")
                    raise ValueError(f"Workspace not found: {name}")
                return workspace
        if id:
            async with self.__async_db_session as async_session:
                db_workspace = await async_session.execute(
                    select(Workspace).filter(Workspace.id == id)
                )
                workspace = db_workspace.scalars().first()

                if not workspace:
                    await self.logger.b_info(f"Workspace not found: {name}")
                    raise ValueError(f"Workspace not found: {name}")
                return workspace
        
    async def get_workspace_by_name(
                self,
                workspace_name: str
        ) -> WorkspaceResponseSchema:
            """
            Retrieves a workspace by its name.
            Args:
                workspace_name (str): Name of the workspace to retrieve.
            Returns:
                WorkspaceResponseSchema: The workspace object.
            Raises:
                ValueError: If the workspace does not exist or there's an issue retrieving it.
            """
            try:
                async with self.__async_db_session as async_session:
                    db_workspace = await async_session.execute(
                        select(Workspace).filter(Workspace.name == workspace_name)
                    )
                    workspace = db_workspace.scalars().first()

                    if not workspace:
                        await self.logger.b_info(f"Workspace not found: {workspace_name}")
                        raise ValueError(f"Workspace not found: {workspace_name}")
                    

                    json_files = workspace.get_all_files_and_dirs()  # This will return a list of FileResponseSchema
                    print(f"json_files: {json_files}")  # Отладочное сообщение
                    # Check if json_files contains an error message
                    if isinstance(json_files, dict) and "error" in json_files:
                        raise HTTPException(status_code=500, detail=json_files["error"])

                    return WorkspaceResponseSchema(
                        id=workspace.id,
                        user_id=workspace.user_id,
                        name=workspace.name,
                        description=workspace.description,
                        is_active=workspace.is_active,
                        is_public=workspace.is_public,
                        files=json_files  # Now correctly structured
                    )

            except ValueError as ve:
                raise HTTPException(status_code=500, detail=str(ve))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
        
    async def get_workspaces(
            self,
            user_id: int
    ) -> list[Any] | list[WorkspaceResponseSchema]:
        """
        Retrieves all workspaces for a given user.
        Args:
            user_id (int): ID of the user whose workspaces are to be retrieved.
        Returns:
            Tuple[Workspace, ...]: A tuple containing all the workspaces owned by the user.
        Raises:
            ValueError: If there's an issue retrieving workspaces.
        """
        try:
            async with self.__async_db_session as async_session:
                db_workspaces = await async_session.execute(select(Workspace).filter(Workspace.user_id == user_id))
                workspaces: List[Workspace] = db_workspaces.scalars().all()

                if not workspaces:
                    await self.logger.b_info(f"No workspaces found for user: {user_id}")
                    return []
                
                return [WorkspaceResponseSchema(
                        id = workspace.id,
                        user_id = workspace.user_id,
                        name = workspace.name,
                        description = workspace.description,
                        is_active = workspace.is_active,
                        is_public = workspace.is_public,
                        files = None
                    ) for workspace in workspaces ]
        except Exception as e:
            await self.logger.b_crit(f"Error retrieving workspaces for user: {user_id} {e}")
            raise ValueError(f"Error retrieving workspaces for user: {user_id} {e}") from e

    async def delete_workspace(self, workspace_name: str, user_id: int):
        try:
            async with self.__async_db_session as async_session:
                    # Найти рабочее пространство по идентификатору и идентификатору пользователя
                    result = await async_session.execute(
                        select(Workspace).filter(Workspace.name == workspace_name, Workspace.user_id == user_id)
                    )
                    workspace = result.scalars().first()
                    workspace.delete_workspace()
                    if workspace:
                        # Удалить рабочее пространство
                        await async_session.delete(workspace)
                        await async_session.commit()
                    else:
                        await self.logger.b_warn(f"Workspace with id {workspace.id} not found for user {user_id}")
                        raise ValueError(f"Workspace with id {workspace.id} not found for user {user_id}")
        except Exception as e:
            await self.logger.b_crit(f"Failed to delete workspace: {e}")
            raise ValueError(f"Failed to delete workspace: {e}")

        except Exception as e:
            await self.logger.b_crit(f"Failed to delete workspace: {e}")
            raise ValueError(f"Failed to delete workspace: {e}")
    async def create_file(self, name: str, workspace: Workspace):
        """
        Создание файла в workspace
        """
        try:
            if workspace.create_file(name):
                await self.logger.b_info(f"File '{name}' created successfully.")
            else:
                raise ValueError(f"File '{name}' already exists or cannot be created.")
        except Exception as e:
            await self.logger.b_crit(f"Error creating file: {e}")
            raise ValueError(f"Error creating file: {e}")
    
    async def create_folder(self, name: str, workspace: Workspace):
        """
        Создание папки в workspace
        """
        try:
            if workspace.create_folder(name):
                await self.logger.b_info(f"Folder '{name}' created successfully.")
            else:
                raise ValueError(f"Folder '{name}' already exists or cannot be created.")
        except Exception as e:
            await self.logger.b_crit(f"Error creating folder: {e}")
            raise ValueError(f"Error creating folder: {e}")

    async def copy_item(self, src: str, dst: str, workspace: Workspace):
        """
        Копирование файла или папки
        """
        try:
            if workspace.copy(src, dst):
                await self.logger.b_info(f"'{src}' copied to '{dst}' successfully.")
            else:
                raise ValueError(f"Failed to copy '{src}' to '{dst}'.")
        except Exception as e:
            await self.logger.b_crit(f"Error copying '{src}' to '{dst}': {e}")
            raise ValueError(f"Error copying '{src}' to '{dst}': {e}")
    
    async def delete_item(self, path: str, workspace: Workspace):
        """
        Удаление файла или папки
        """
        try:
            if workspace.delete(path):
                await self.logger.b_info(f"'{path}' deleted successfully.")
            else:
                raise ValueError(f"Failed to delete '{path}'.")
        except Exception as e:
            await self.logger.b_crit(f"Error deleting '{path}': {e}")
            raise ValueError(f"Error deleting '{path}': {e}")

    async def rename_item(self, old_name: str, new_name: str, workspace: Workspace):
        """
        Переименование файла или папки
        """
        try:
            if workspace.rename(old_name, new_name):
                await self.logger.b_info(f"'{old_name}' renamed to '{new_name}' successfully.")
            else:
                raise ValueError(f"Failed to rename '{old_name}' to '{new_name}'.")
        except Exception as e:
            await self.logger.b_crit(f"Error renaming '{old_name}' to '{new_name}': {e}")
            raise ValueError(f"Error renaming '{old_name}' to '{new_name}': {e}")

    async def edit_file(self, file: str, content: str, workspace: Workspace):
        """
        Редактирование содержимого файла
        """
        try:
            if workspace.edit_file(file, content):
                await self.logger.b_info(f"File '{file}' edited successfully.")
            else:
                raise ValueError(f"Failed to edit file '{file}'.")
        except Exception as e:
            await self.logger.b_crit(f"Error editing file '{file}': {e}")
            raise ValueError(f"Error editing file '{file}': {e}")
        
    async def open_file(self, file: str, workspace: Workspace) -> str:
        """
        Возвращаем данные из файла 
        """
        try:
            data = workspace.open_file(file)
            if data:
                await self.logger.b_info(f"File '{file}' opened successfully.")
            else:
                raise ValueError(f"Failed to open file '{file}'.")
        except Exception as e:
            await self.logger.b_crit(f"Error opening file '{file}': {e}")
            raise ValueError(f"Error opening file '{file}': {e}")
        return data

    async def open_file(self, file: str, workspace: Workspace) -> str:
        """
        Возвращаем данные из файла 
        """
        try:
            data = workspace.open_file(file)
            if data:
                await self.logger.b_info(f"File '{file}' opened successfully.")
            else:
                raise ValueError(f"Failed to open file '{file}'.")
        except Exception as e:
            await self.logger.b_crit(f"Error opening file '{file}': {e}")
            raise ValueError(f"Error opening file '{file}': {e}")
        return data

    async def execute_user_code(self, response, user):
        """
        This method is implemented testing code runner for nonlogin users
        Args:
            - code: Code for executing
            - language: Language code for executing
        Returns:
            - CodeExecute
        """
        if response.language not in self.USING_LANGUAGE:
            return {
                'output': "",
                "error": "This language is not available now"
            }

        try:
            output, error = await self.execute_code(response.code, response.language, user)
            if not output and not error:
                error = "No output or error returned from execution"
        except subprocess.CalledProcessError as e:
            output = ''
            error = str(e)
        except Exception as e:
            output = ''
            error = str(e)

        return {
            'output': output,
            'error': error,
        }

    @contextmanager
    def create_code_file(self, path: str, text: str):
        with open(path, "w") as file:
            file.write(text)
        yield
        # os.remove(path) Optional

    async def execute_code(self, code: str, language: str, user: User) -> Tuple[str, Union[str, None]]:
        user_dir = f"{os.getcwd()}/storage/{user.username}_{user.uuid_file_store}/projects"
        os.makedirs(user_dir, exist_ok=True)
        params = {
            'language': language,
            'code': code,
            'user_dir': user_dir
        }

        print(f"Executing code with params: {params}")  # Отладочное сообщение

        if not params:
            return "", "Invalid parameters"
        if params['language'] == 'python':
            return self.execute_python_code(params)
        if params['language'] == 'c':
            return self.execute_c_code(params)
        if params['language'] == 'cpp':
            return self.execute_cpp_code(params)
        if params['language'] == 'js':
            return self.execute_js_code(params)
        if params['language'] == 'cs':
            return await self.execute_cs_code(params)
        if params['language'] == 'go':
            return self.execute_golang_code(params)
        if params['language'] == 'ruby':
            return self.execute_ruby_code(params)
        else:
            return "", "Unsupported language"

    def run_docker_container(self, image: str, command: str, user_dir: str) -> Tuple[str, Union[str, None]]:
        client = docker.from_env()
        try:
            result = client.containers.run(
                image,
                command,
                volumes={os.path.abspath(user_dir): {'bind': '/usr/src/app', 'mode': 'rw'}},
                working_dir='/usr/src/app',
                detach=False,
                stdout=True,
                stderr=True
            )
            output = result.decode('utf-8').strip()
            error = None
        except docker.errors.ContainerError as e:
            output = e.stderr.decode('utf-8').strip() if e.stderr else ''
            error = f"Command '{e.command}' in image '{e.image}' returned non-zero exit status {e.exit_status}: {output}"
        except docker.errors.ImageNotFound as e:
            output = ''
            error = f"Image not found: {e}"
        except docker.errors.APIError as e:
            output = ''
            error = f"Docker API error: {e}"
        except Exception as e:
            output = ''
            error = str(e)

        # Отладочная информация
        print(f"Docker container output: {output}")
        print(f"Docker container error: {error}")

        return output, error or None
    
    def execute_python_code(self, params: dict) -> Tuple[str, Union[str, None]]:
        code = params['code']
        user_dir = params['user_dir']
        path = os.path.join(user_dir, "code.py")
        with self.create_code_file(path, code):
            container_path = "/usr/src/app/code.py"  # Путь внутри контейнера
            return self.run_docker_container("python:3.9", f"python {container_path}", user_dir)

    def execute_c_code(self, params: dict) -> Tuple[str, Union[str, None]]:
        code = params['code']
        user_dir = params['user_dir']

        # Create file with .c extension and UUID name
        c_file_path = os.path.join(user_dir, f"{str(uuid.uuid4())}.c")
        container_path = f"/usr/src/app/{os.path.basename(c_file_path)}"  # Dynamically use the created file's name

        # Create the file
        with self.create_code_file(c_file_path, code):
            print(f"Creating C file at {c_file_path} and running container with command: gcc {container_path} -o /tmp/code && /tmp/code")

            # Run the container and compile the file using the correct path
            return self.run_docker_container(
                "gcc:latest",
                f"sh -c 'gcc {container_path} -o /tmp/code && /tmp/code'",
                user_dir
            )

    def execute_cpp_code(self, params: dict) -> Tuple[str, Union[str, None]]:
        code = params['code']
        user_dir = params['user_dir']

        # Create file with .cpp extension and UUID name
        cpp_file_path = os.path.join(user_dir, f"{str(uuid.uuid4())}.cpp")
        container_path = f"/usr/src/app/{os.path.basename(cpp_file_path)}"  # Dynamically use the created file's name

        # Create the file
        with self.create_code_file(cpp_file_path, code):
            print(f"Creating C++ file at {cpp_file_path} and running container with command: g++ {container_path} -o /tmp/code && /tmp/code")

            # Run the container and compile the file using the correct path
            return self.run_docker_container(
                "gcc:latest",
                f"sh -c 'g++ {container_path} -o /tmp/code && /tmp/code'",
                user_dir
            )
            
    def execute_js_code(self, params: dict) -> Tuple[str, Union[str, None]]:
        code = params['code']
        user_dir = params['user_dir']

        # Generate a unique .js file path
        js_file_path = os.path.join(user_dir, f"{str(uuid.uuid4())}.js")
        container_path = f"/usr/src/app/{os.path.basename(js_file_path)}"  # Use dynamic file name in container

        # Create the JavaScript file
        with self.create_code_file(js_file_path, code):
            print(f"Creating JS file at {js_file_path} and running container with command: node {container_path}")

            # Run the container with the correct path to the file
            return self.run_docker_container("node:latest", f"node {container_path}", user_dir)


    async def execute_cs_code(self, params: dict) -> Tuple[str, Union[str, None]]:
        code = params['code']
        user_dir = params['user_dir']
        path = os.path.join(user_dir, "cs_project")
        code_file_path = os.path.join(path, f"{str(uuid.uuid4())}.cs")
        os.makedirs(path, exist_ok=True)

        with self.create_code_file(code_file_path, code):
            container_path = "/usr/src/app/cs_project"

            # Run Docker and capture the output/error with verbosity
            output, error = self.run_docker_container(
                "mcr.microsoft.com/dotnet/sdk:latest",
                f"sh -c 'dotnet new console -o {container_path} --force && dotnet build {container_path} -v diag && dotnet run --project {container_path}'",
                user_dir
            )

            if error:
                await self.logger.b_err(f"Error during Docker execution: {error}")
                if "dotnet new console" in error:
                    await self.logger.b_err("Failed at 'dotnet new console' step.")
                elif "dotnet build" in error:
                    await self.logger.b_err("Failed at 'dotnet build' step.")
                elif "dotnet run" in error:
                    await self.logger.b_err("Failed at 'dotnet run' step.")
            else:
                await self.logger.b_info(f"Docker output: {output}")

            return output, error

    def execute_ruby_code(self, params: dict) -> Tuple[str, Union[str, None]]:
        code = params['code']
        user_dir = params['user_dir']
        path = os.path.join(user_dir, f"{str(uuid.uuid4())}.rb")
        with self.create_code_file(path, code):
            container_path = f"/usr/src/app/{os.path.basename(path)}"  # Use dynamic file name in container
            return self.run_docker_container("ruby:latest", f"ruby {container_path}", user_dir)

    def execute_golang_code(self, params: dict) -> Tuple[str, Union[str, None]]:
        code = params['code']
        user_dir = params['user_dir']
        path = os.path.join(user_dir, f"{str(uuid.uuid4())}.go")
        go_mod_path = os.path.join(user_dir, "go.mod")

        # # Create go.mod file
        # go_mod_content = """
        # module usercode

        # go 1.16
        # """
        # with self.create_code_file(go_mod_path, go_mod_content):
        #     pass

        with self.create_code_file(path, code):
            container_path = "/usr/src/app/code.go"  # Path inside the container
            return self.run_docker_container("golang:latest", f"sh -c 'cd /usr/src/app && go mod init usercode && go build {container_path} && ./code'", user_dir)
        
        
    async def get_abs_file_path(self, workspace_path: str, filename: str) -> str:
        abs_path = os.path.join(workspace_path, filename)
        
        # Защита от атак через '../'
        if not abs_path.startswith(workspace_path):
            raise HTTPException(
                status_code=400,
                detail="Invalid path"
            )
        return abs_path