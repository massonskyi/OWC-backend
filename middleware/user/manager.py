import shutil
from typing import Tuple, Union, Any
from typing import Optional # noqa: F401
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError


from core.const import DEFAULT_USER_AVATAR_PATH


from middleware.utils import PasswordManager, create_access_token
from middleware.user.schemas import UserCreateSchema, WorkspaceSchema, WorkspaceResponseSchema, Token
from middleware.user.models import User, UserToken
import io
import os
import subprocess
from contextlib import redirect_stdout
from typing import Any
from sqlalchemy import select
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
            projects = user.create_projects(workspace.id)
            if not projects:
                await self.logger.b_crit(f"Failed to create projects, projects = {projects}")
                raise ValueError("Failed to create projects, projects = {projects}")

            
            async with self.__async_db_session as async_session:
                async with async_session.begin():
                    for project in projects:
                        async_session.add(project)
                    await async_session.commit()  
                    
        except Exception as e:
            await self.logger.b_crit(f"Failed to create projects: {e}")
            raise ValueError(f"Failed to create projects: {e}")

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

    async def verify_user(
        self, 
        login: str, 
        password: str
    ) -> Union[UserCreateSchema, None]:
        """
        Verify the user with the given login and password.

        Args:
            login: The user's login.
            password: The user's password.

        Returns:
            The User object if the login and password are correct, or None otherwise.
        """
        async with self.__async_db_session as session:
            user = await session.execute(select(User).filter(User.login == login))
            user = user.scalars().first()
            if user and self.password_manager.verify(user.hash_password, password):
                return UserCreateSchema(**user.to_dict())
            
            return None

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

    async def create_workspace(
            self,
            user_id: int = None,
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
            user_id=user_id,
            description=new.description,
            is_active=True,
            is_public=new.is_public,
        )

        try:
            # Add the new workspace to the database
            async with self.__async_db_session as async_session:
                async with async_session.begin():
                    async_session.add(new_workspace)
                    await async_session.commit()
        except Exception as e:
            await self.logger.b_crit(f"Error creating workspace: {new}")
            raise ValueError(f"Error creating workspace: {new}") from e

        return WorkspaceResponseSchema(**new_workspace.to_dict())

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
                workspaces = db_workspaces.scalars().all()

                if not workspaces:
                    await self.logger.b_info(f"No workspaces found for user: {user_id}")
                    return []

                return [WorkspaceResponseSchema(**workspace.to_dict()) for workspace in workspaces]
        except Exception as e:
            await self.logger.b_crit(f"Error retrieving workspaces for user: {user_id}")
            raise ValueError(f"Error retrieving workspaces for user: {user_id}") from e

    async def delete_workspace(
            self,
            user_id: int,
            workspace_id: int
    ) -> None:
        """
        Deletes a workspace by its ID.
        Args:
            user_id (int): ID of the user who owns the workspace.
            workspace_id (int): The ID of the workspace to delete.
        Returns:
            None
        Raises:
            ValueError: If the workspace does not exist or the deletion fails.
        """
        try:
            async with self.__async_db_session as async_session:
                db_workspace = await async_session.execute(
                    select(Workspace)
                    .filter(Workspace.id == workspace_id, Workspace.user_id == user_id)
                )
                db_workspace = db_workspace.scalars().first()

                if not db_workspace:
                    await self.logger.b_crit(f"Workspace not found for deletion: {workspace_id}")
                    raise ValueError(f"Workspace not found: {workspace_id}")

                async with async_session.begin():
                    await async_session.delete(db_workspace)
                    await async_session.commit()

                await self.logger.b_info(f"Workspace deleted: {workspace_id}")
        except Exception as e:
            await self.logger.b_crit(f"Error deleting workspace: {workspace_id}")
            raise ValueError(f"Error deleting workspace: {workspace_id}") from e

    async def test_exec(self, response):
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
            output, error = self.execute_code(response)
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

    def create_code_file(self, path: str, text: str = None) -> bool:
        if not text:
            return False

        with open(path, "w") as file:
            file.write(text)

        return True

    def execute_code(self, code: str, language: str) -> [str, str or None]:
        params = {
            'language': language,
            'code': code
        }

        if not params:
            return "", ""
        if params['language'] == 'python':
            return self.execute_python_code(params['code'])
        if params['language'] == 'c' or params['language'] == 'cpp':
            return self.execute_c_code(params)
        if params['language'] == 'js':
            return self.execute_js_code(params)
        if params['language'] == 'cs':
            return self.execute_cs_code(params)
        if params['language'] == 'go':
            return self.execute_golang_code(params)
        if params['language'] == 'ruby':
            return self.execute_ruby_code(params)
        else:
            raise Exception('Unsupported language')

    def execute_python_code(self, code: str) -> [str, str or None]:
        f = io.StringIO()
        with redirect_stdout(f):
            exec(code, {}, {'output': None})
        output = f.getvalue().strip()
        return [output, None]

    def execute_c_code(self, params: dict) -> [str, str or None]:
        if not params or len(params) == 0:
            raise ValueError("params is none or params len = 0")
        language: str = params['language']
        code: str = params['code']

        path: str = f"builds/{language}/code.{language}"

        # Write the code to a file
        self.create_code_file(path, code)

        # Compile the code
        compiler = "g++" if language == "cpp" else "gcc"
        cmd: list[str] = [compiler, path, '-o', f"builds/{language}/code"]
        subprocess.run(cmd, check=True)

        # Execute the compiled code
        execute_cmd: list[str] = [f"builds/{language}/code"]
        process: subprocess.CompletedProcess[str] = subprocess.run(
            execute_cmd, capture_output=True, text=True)
        return [process.stdout.strip(), process.stderr.strip() or None]

    def execute_js_code(self, params: dict) -> [str, str or None]:
        if not params or len(params) == 0:
            raise ValueError("params is none or params len = 0")
        language: str = params['language']
        code: str = params['code']

        path: str = f"builds/{language}/code.{language}"

        # Write the code to a file
        self.create_code_file(path, code)
        # Execute the compiled code
        execute_cmd: list[str] = ['node', path]
        process: subprocess.CompletedProcess[str] = subprocess.run(
            execute_cmd, capture_output=True, text=True)
        return [process.stdout.strip(), process.stderr.strip() or None]

    def execute_cs_code(self, params: dict) -> [str, str or None]:
        if not params or len(params) == 0:
            raise ValueError("params is none or params len = 0")

        language: str = params['language']
        code: str = params['code']

        path: str = f"builds/{language}"
        code_file_path = f"{path}/Program.cs"

        # Create the directories if necessary
        os.makedirs(path, exist_ok=True)

        # Create a new C# console application
        subprocess.run(['dotnet', 'new', 'console', '-o',
                        path, '--force'], check=True)
        # Write the code to a file
        self.create_code_file(code_file_path, code)
        # Compile the code
        cmd: list[str] = ['dotnet', 'build', path]
        subprocess.run(cmd, check=True)

        # Execute the compiled code
        execute_cmd: list[str] = ['dotnet', 'run', '--project', path]
        process: subprocess.CompletedProcess[str] = subprocess.run(
            execute_cmd, capture_output=True, text=True)

        return [process.stdout.strip(), process.stderr.strip() or None]

    def execute_ruby_code(self, params: dict) -> [str, str or None]:
        if not params or len(params) == 0:
            raise ValueError("params is none or params len = 0")

        language: str = params['language']
        code: str = params['code']

        path: str = f"builds/{language}/code.ruby"
        # Write the code to a file
        self.create_code_file(path, code)
        # Execute the compiled code
        execute_cmd: list[str] = ['ruby', path]
        process: subprocess.CompletedProcess[str] = subprocess.run(
            execute_cmd, capture_output=True, text=True)

        return [process.stdout.strip(), process.stderr.strip() or None]

    def execute_golang_code(self, params: dict) -> [str, str or None]:
        if not params or len(params) == 0:
            raise ValueError("params is none or params len = 0")
        language: str = params['language']
        code: str = params['code']

        path: str = f"builds/{language}/code.{language}"

        # Write the code to a file
        self.create_code_file(path, code)
        # Compile the code
        cmd: list[str] = ['go', 'build',
                          path]
        subprocess.run(cmd, check=True)
        # Execute the compiled code
        execute_cmd: list[str] = [cfg.get('COMPILER', f'{language}'), 'run',
                                  f"builds/{language}"]
        process: subprocess.CompletedProcess[str] = subprocess.run(
            execute_cmd, capture_output=True, text=True)

        return [process.stdout.strip(), process.stderr.strip() or None]
