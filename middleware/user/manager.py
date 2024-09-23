import shutil
import uuid
import docker
from typing import Tuple, Union, Any
from typing import Optional
from typing_extensions import deprecated # noqa: F401
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError


from core.const import DEFAULT_USER_AVATAR_PATH


from middleware.utils import PasswordManager, create_access_token
from middleware.user.schemas import ProjectResponseSchema, ProjectSchema, UserCreateSchema, WorkspaceSchema, WorkspaceResponseSchema, Token
from middleware.user.models import Project, User, UserToken
import io
import os
import subprocess
from contextlib import contextmanager, redirect_stdout
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
        
        return WorkspaceResponseSchema(**new_workspace.to_dict())
    
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
        
    async def create_project(
            self,
            user: User = None,
            new: ProjectSchema = None,
    ) -> ProjectResponseSchema:
        """
        Creates a new project.
        Args:
            user (User): The user who owns the project.
            new (ProjectSchema): The project to be created.
        Returns:
            ProjectResponseSchema: The created project.
        Raises:
            ValueError: If the project creation fails.
        """
        new_project = Project(
            name=new.name,
            workspace_id=new.workspace_id,
            description=new.description,
            language=new.language,
            is_active=new.is_active,
            path=new.path,
        )
        try:
            async with self.__async_db_session as async_session:
                if not async_session.in_transaction():
                    async with async_session.begin():
                        async_session.add(new_project)
                        await async_session.commit()
                else:
                    async_session.add(new_project)
                    await async_session.commit()
                
        except SQLAlchemyError as e:
            await self.logger.b_crit(f"SQLAlchemyError: {e}")
            raise ValueError(f"Error creating project: {new}")
        
        except Exception as e:
            await self.logger.b_crit(f"Error creating project: {new}")
            raise ValueError(f"Error creating project: {new}")
        
        return ProjectResponseSchema(**new_project.to_dict())
    
    async def update_project(
            self,
            user_id: int,
            project_id: int,
            updated_data: ProjectSchema
    ) -> ProjectResponseSchema:
        """
        Updates an existing project.
        Args:
            user_id (int): ID of the user who owns the project.
            project_id (int): The ID of the project to update.
            updated_data (ProjectSchema): The updated project data.
        Returns:
            ProjectResponseSchema: The updated project.
        Raises:
            ValueError: If the project does not exist or the update fails.
        """
        try:
            async with self.__async_db_session as async_session:
                db_project = await async_session.execute(
                    select(Project)
                    .where(Project.id == project_id, Project.workspace_id == updated_data.workspace_id)
                )
                db_project = db_project.scalars().first()

                if db_project is None:
                    await self.logger.b_crit(f"Project not found: {project_id}")
                    raise ValueError(f"Project not found: {project_id}")

                # Обновляем данные проекта
                db_project.name = updated_data.name
                db_project.description = updated_data.description
                db_project.language = updated_data.language
                db_project.is_active = updated_data.is_active
                db_project.path = updated_data.path

                async with async_session.begin():
                    await async_session.commit()

                return ProjectResponseSchema(**db_project.to_dict())

        except SQLAlchemyError as e:
            await self.logger.b_crit(f"SQLAlchemyError: {e}")
            raise ValueError(f"Error updating project: {project_id}")

        except Exception as e:
            await self.logger.b_crit(f"Error updating project: {project_id}")
            raise ValueError(f"Error updating project: {project_id}") from e
        
    async def get_last_project(
            self,
            workspace_id: int
    ) -> Project:
        """
        Get the last project created in the workspace.

        Args:
            workspace_id (int): The ID of the workspace.

        Returns:
            Project: The last project created in the workspace.

        Raises:
            ValueError: If the project does not exist.
        """
        try:
            async with self.__async_db_session as async_session:
                db_project = await async_session.execute(
                    select(Project)
                    .where(Project.workspace_id == workspace_id)
                    .order_by(Project.created_at.desc())
                    .limit(1)
                )
                db_project = db_project.scalars().first()

                if db_project is None:
                    await self.logger.b_crit(f"No projects found for workspace: {workspace_id}")
                    raise ValueError(f"No projects found for workspace: {workspace_id}")

                return db_project

        except Exception as e:
            await self.logger.b_crit(f"Error retrieving last project for workspace: {workspace_id}")
            raise ValueError(f"Error retrieving last project for workspace: {workspace_id}") from e

    async def get_project(
            self,
            workspace_id: int,
            project_id: int
    ) -> ProjectResponseSchema:
        """
        Gets a project by its ID.
        Args:
            workspace_id (int): ID of the workspace.
            project_id (int): The ID of the project to retrieve.
        Returns:
            ProjectResponseSchema: The retrieved project.
        Raises:
            ValueError: If the project does not exist.
        """
        try:
            async with self.__async_db_session as async_session:
                db_project = await async_session.execute(
                    select(Project)
                    .where(Project.id == project_id, Project.workspace_id == workspace_id)
                )
                db_project = db_project.scalars().first()

                if db_project is None:
                    await self.logger.b_crit(f"Project not found: {project_id}")
                    raise ValueError(f"Project not found: {project_id}")

                return ProjectResponseSchema(**db_project.to_dict())

        except Exception as e:
            await self.logger.b_crit(f"Error retrieving project: {project_id}")
            raise ValueError(f"Error retrieving project: {project_id}") from e

    async def get_projects(
            self,
            workspace_id: int
    ) -> list[Any] | list[ProjectResponseSchema]:
        """
        Retrieves all projects for a given workspace.
        Args:
            workspace_id (int): ID of the workspace whose projects are to be retrieved.
        Returns:
            list[ProjectResponseSchema]: A list containing all the projects in the workspace.
        Raises:
            ValueError: If there's an issue retrieving projects.
        """
        try:
            async with self.__async_db_session as async_session:
                db_projects = await async_session.execute(select(Project).filter(Project.workspace_id == workspace_id))
                projects = db_projects.scalars().all()

                if not projects:
                    await self.logger.b_info(f"No projects found for workspace: {workspace_id}")
                    return []

                return [ProjectResponseSchema(**project.to_dict()) for project in projects]
        except Exception as e:
            await self.logger.b_crit(f"Error retrieving projects for workspace: {workspace_id}")
            raise ValueError(f"Error retrieving projects for workspace: {workspace_id}") from e

    async def delete_project(
            self,
            workspace_id: int,
            project_id: int
    ) -> None:
        """
        Deletes a project by its ID.
        Args:
            workspace_id (int): ID of the workspace.
            project_id (int): The ID of the project to delete.
        Returns:
            None
        Raises:
            ValueError: If the project does not exist or the deletion fails.
        """
        try:
            async with self.__async_db_session as async_session:
                db_project = await async_session.execute(
                    select(Project)
                    .filter(Project.id == project_id, Project.workspace_id == workspace_id)
                )
                db_project = db_project.scalars().first()

                if not db_project:
                    await self.logger.b_crit(f"Project not found for deletion: {project_id}")
                    raise ValueError(f"Project not found: {project_id}")

                async with async_session.begin():
                    await async_session.delete(db_project)
                    await async_session.commit()

                await self.logger.b_info(f"Project deleted: {project_id}")
        except Exception as e:
            await self.logger.b_crit(f"Error deleting project: {project_id}")
            raise ValueError(f"Error deleting project: {project_id}") from e
        

    async def test_exec(self, response, user):
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
            output, error = self.execute_code(response.code, response.language, user)
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

    def execute_code(self, code: str, language: str, user: User) -> Tuple[str, Union[str, None]]:
        user_dir = f"{os.getcwd()}/storage/{user.username}_{user.uuid_file_store}/tmp/projects"
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
            output = e.stderr.decode('utf-8').strip()
            error = f"Command '{e.command}' in image '{e.image}' returned non-zero exit status {e.exit_status}: {output}"
        except Exception as e:
            output = ''
            error = str(e)
        
        print(f"Docker container output: {output}")  # Отладочное сообщение
        print(f"Docker container error: {error}")  # Отладочное сообщение
        return [output, error or None]

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
        path = os.path.join(user_dir, f"{str(uuid.uuid4())}.c")
        with self.create_code_file(path, code):
            container_path = "/usr/src/app/code.c"  # Путь внутри контейнера
            return self.run_docker_container("gcc:latest", f"sh -c 'gcc {container_path} -o /tmp/code && /tmp/code'", user_dir)

    def execute_js_code(self, params: dict) -> Tuple[str, Union[str, None]]:
        code = params['code']
        user_dir = params['user_dir']
        path = os.path.join(user_dir, f"{str(uuid.uuid4())}.js")
        with self.create_code_file(path, code):
            container_path = "/usr/src/app/code.js"  # Путь внутри контейнера
            return self.run_docker_container("node:latest", f"node {container_path}", user_dir)

    def execute_cs_code(self, params: dict) -> Tuple[str, Union[str, None]]:
        code = params['code']
        user_dir = params['user_dir']
        path = os.path.join(user_dir, "cs_project")
        code_file_path = os.path.join(path, f"{str(uuid.uuid4())}.cs")
        os.makedirs(path, exist_ok=True)
        with self.create_code_file(code_file_path, code):
            container_path = "/usr/src/app/cs_project"  # Путь внутри контейнера
            return self.run_docker_container(
                "mcr.microsoft.com/dotnet/sdk:latest",
                f"sh -c 'dotnet new console -o {container_path} --force && dotnet build {container_path} && dotnet run --project {container_path}'",
                user_dir
            )

    def execute_ruby_code(self, params: dict) -> Tuple[str, Union[str, None]]:
        code = params['code']
        user_dir = params['user_dir']
        path = os.path.join(user_dir, f"{str(uuid.uuid4())}.rb")
        with self.create_code_file(path, code):
            container_path = "/usr/src/app/code.rb"  # Путь внутри контейнера
            return self.run_docker_container("ruby:latest", f"ruby {container_path}", user_dir)

    def execute_golang_code(self, params: dict) -> Tuple[str, Union[str, None]]:
        code = params['code']
        user_dir = params['user_dir']
        path = os.path.join(user_dir, f"{str(uuid.uuid4())}.go")
        with self.create_code_file(path, code):
            container_path = "/usr/src/app/code.go"  # Путь внутри контейнера
            return self.run_docker_container("golang:latest", f"sh -c 'go build {container_path} && {container_path}'", user_dir)