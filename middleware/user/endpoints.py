from contextlib import contextmanager
from datetime import  datetime, timedelta
import json
import os
import subprocess
import uuid

import docker
from fastapi import (
    APIRouter, 
    Depends,
    Form,
    HTTPException, 
    status,
    Response

)
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm


from sqlalchemy.ext.asyncio import AsyncSession


from database.session import get_async_db


from middleware import ACCESS_TOKEN_EXPIRE_MINUTES
from middleware.user.manager import UserManager
from middleware.user.models import User

from middleware.user.schemas import (
    CodeSchema,
    UserCreateSchema,
    Token,
    UserLoginSchema,
    WorkspaceResponseSchema, WorkspaceSchema
)
from typing import Any, Optional, Tuple, Union # noqa: F401

from middleware.utils import create_access_token, get_current_user

UserCreateResponse,\
TokenResponse,\
UserLoginResponse = UserCreateSchema,\
                    Token,\
                    UserLoginSchema


API_USER_MODULE = APIRouter(
    prefix="/user",
    tags=["User & workspaces/projects module for Online Workspace Code for you"],
)

async def get_user_manager(
    db_session: AsyncSession = Depends(get_async_db)
) -> 'UserManager':
    """
    Get order manager instance.
    @params:
            db_session: database session.
    @return:
            order manager instance.

    @raise: HTTPException if order manager instance not found.
    """
    return UserManager(db_session)

@API_USER_MODULE.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), user_manager: 'UserManager' = Depends(get_user_manager)):
    user,_,_= await user_manager.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token, expire = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    response = Response(
        content=json.dumps({"access_token": access_token, "token_type": "bearer", "expires_at": expire.isoformat()}),
        media_type="application/json"
    )
    response.set_cookie(
        key="token",
        value=access_token,
        httponly=True,
        samesite="Lax",
        secure=False,
        max_age=int(access_token_expires.total_seconds())  # Используем total_seconds() для получения времени в секундах
    )
    return response
@API_USER_MODULE.post(
    '/sign_up', 
    response_model=UserCreateSchema,
    summary="Sign up user to the system",
)
async def sign_up(
    new: UserCreateSchema = Depends(),
    user_manager: 'UserManager' = Depends(get_user_manager)
) -> Response:
    """
    Sign up user to the system and return the token to be used to login in the future.
    """
    status_code: status    
    response_content = {}
    user, access_token, expire = None, None, datetime.now()
    try:
        user, access_token, expire = await user_manager.create_user(new)
    except ValueError as val_err:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(
            status_code=status_code, 
            detail=str(val_err)
        )
        
    except Exception as e:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(
            status_code=status_code, 
            detail=str(e)
        )
        
    else:
        response_content['user'] = user.to_dict()
        response_content['token'] = access_token
        response_content['token_expires_at'] = expire.timestamp()
        response_content['message'] = "User created successfully"
        status_code = status.HTTP_201_CREATED
    # finally:
        
    #     if not response_content.get('user', None):
    #         status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    #         response_content['user'] = None
    #         response_content['token'] = None
    #         response_content['token_expires_at'] = None
    #         response_content['message'] = "User created error"

        response_json = json.dumps(response_content)
        response = Response(content=response_json, media_type="application/json", status_code=status_code)

        if access_token and expire:
            current_time = datetime.utcnow()
            time_delta = expire - current_time  # Получаем объект timedelta
            max_age = int(time_delta.total_seconds())  # Применяем метод total_seconds()
            # Set the cookie
            response.set_cookie(
                key="token",
                value=access_token,
                httponly=True,
                samesite="Lax",
                secure=False,
                max_age=int(max_age)  # Используем total_seconds() для получения времени в секундах
            )

        # # Optional: Add custom headers if needed
        # response.headers['X-Custom-Header'] = 'Value'

        return response



@API_USER_MODULE.post(
    '/sign_in', 
    response_model=UserLoginSchema,
    summary="Sign in user to the system",
)
async def sign_in(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    user_manager: 'UserManager' = Depends(get_user_manager)
) -> Response:
    """
    Sign in user to the system and return the token to be used for authentication.
    """
    status_code: status    
    response_content = {}
    user, access_token, expire = None, None, datetime.now()
    try:
        # Аутентификация пользователя
        user, access_token, expire = await user_manager.authenticate_user(form_data.username, form_data.password)
        if not access_token or not user:
            status_code = status.HTTP_400_BAD_REQUEST
            raise HTTPException(
                status_code=status_code, 
                detail="Incorrect email or password"
            )
        
        # Проверка, если токен истек, генерируем новый токен
        current_time = datetime.now()  # Change this to get the current datetime
        if expire < current_time:  # Now both are datetime objects
            access_token, expire = await user_manager.generate_new_token(user.id)

    except Exception as e:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(
            status_code=status_code, 
            detail=str(e)
        )
        
    else:
        response_content['user'] = user.to_dict()
        response_content['token'] = access_token
        response_content['token_expires_at'] = expire.timestamp()
        response_content['message'] = "User authenticated successfully"
        status_code = status.HTTP_200_OK
        
    finally:
        if not response_content.get('user', None):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            response_content['user'] = None
            response_content['token'] = None
            response_content['token_expires_at'] = None
            response_content['message'] = "User authentication error"
            
        response_json = json.dumps(response_content)  # Конвертируем ответ в JSON
        response = Response(content=response_json, media_type="application/json", status_code=status_code)

        if access_token and expire:
            response.set_cookie(
                key="token",
                value=access_token,
                expires= expire.timestamp(),
                secure=False,
                httponly=True,
                samesite="Lax",
                path="/",
                domain="localhost"
            )
        return response


@API_USER_MODULE.post(
    '/workspaces/create',
    summary="Create a new workspace",
)
async def create_workspace(
        new: WorkspaceSchema = Depends(),
        workspace_manager: UserManager = Depends(get_user_manager),
        current_user: User = Depends(get_current_user)
) -> Response:
    status_code = None
    response_content = {}
    try:
        workspace = await workspace_manager.create_workspace(current_user, new)

    except Exception as e:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )
    else:
        response_content['workspace'] = workspace.dict()
        response_content['message'] = "Workspace created successfully"
        status_code = status.HTTP_201_CREATED
    finally:
        response_json = json.dumps(response_content)
        return Response(content=response_json, media_type="application/json", status_code=status_code)

@API_USER_MODULE.post(
    '/workspaces/{workspace_id}',
    summary="Get workspace by ID",
)
async def get_workspace(
        workspace_id: Optional[int],
        workspace_manager: UserManager = Depends(get_user_manager),
        current_user: User = Depends(get_current_user)
) -> Response:
    """
    Retrieve a workspace by its ID for the user.
    """

    status_code = None
    response_content = {}
    if workspace_id is None:
        status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
            detail=str("workspace id is not found")
        )
    try:

        workspace = await workspace_manager.get_workspace(current_user.id, workspace_id)
    except ValueError as val_err:
        status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
            detail=str(val_err)
        )
    except Exception as e:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )
    else:
        response_content['workspace'] = workspace.dict()
        response_content['message'] = "Workspace retrieved successfully"
        status_code = status.HTTP_200_OK
    finally:
        response_json = json.dumps(response_content)
        return Response(content=response_json, media_type="application/json", status_code=status_code)

@API_USER_MODULE.get(
    "/workspaces/name/{workspace_name}",
    response_model=WorkspaceResponseSchema,
    summary="Get workspace by name",
)
async def get_workspace_by_name(
    workspace_name: str,
    workspace_manager: UserManager = Depends(get_user_manager),
    current_user: User = Depends(get_current_user)
) -> WorkspaceSchema:
    """
    Retrieve a workspace by its name.
    :param workspace_manager: Workspace manager instance. Used to get workspace.
    :param workspace_name: Name of the workspace to retrieve.
    :return: Workspace object in JSON format.
    """
    try:
        workspace = await workspace_manager.get_workspace_by_name(workspace_name)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        

        return workspace
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@API_USER_MODULE.get(
    '/workspaces/{workspace_name}/file/{filename}', 
    summary="Open a file in a workspace"
)
async def open_file(
        workspace_name: str,
        filename: str,
        workspace_manager: UserManager = Depends(get_user_manager),
        current_user: User = Depends(get_current_user)
) -> Any:
    try:
        workspace = await workspace_manager.get_workspace(name=workspace_name)
        file_contents = await workspace_manager.open_file(filename, workspace)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    return JSONResponse(content={"contents": file_contents}, status_code=status.HTTP_200_OK)
@API_USER_MODULE.get(
    '/workspaces',
    summary="Get all workspaces for the user",
)
async def get_workspaces(
        workspace_manager: UserManager = Depends(get_user_manager),
        current_user: User = Depends(get_current_user)
) -> Response:
    """
    Retrieve all workspaces for the user.
    """
    status_code = None
    response_content = {}
    try:
        workspaces = await workspace_manager.get_workspaces(current_user.id)
    except Exception as e:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )
    else:
        response_content['workspaces'] = [ws.dict() for ws in workspaces]
        response_content['message'] = "Workspaces retrieved successfully"
        status_code = status.HTTP_200_OK
    finally:
        response_json = json.dumps(response_content)
        return Response(content=response_json, media_type="application/json", status_code=status_code)


@API_USER_MODULE.delete(
    '/workspaces/{workspace_name}',
    summary="Delete workspace by ID",
)
async def delete_workspace(
        workspace_id: str,
        workspace_manager: UserManager = Depends(get_user_manager),
        current_user: User = Depends(get_current_user)
) -> Response:
    """
    Delete a workspace by its ID for the user.
    """
    status_code = None
    response_content = {}
    try:
        await workspace_manager.delete_workspace(current_user.id, workspace_id)
    except ValueError as val_err:
        status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
            detail=str(val_err)
        )
    except Exception as e:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )
    else:
        response_content['message'] = "Workspace deleted successfully"
        status_code = status.HTTP_200_OK
    finally:
        response_json = json.dumps(response_content)
        return Response(content=response_json, media_type="application/json", status_code=status_code)


@API_USER_MODULE.post(
    '/workspaces/{workspace_name}/file', 
    summary="Create a file in a workspace"
)
async def create_file(
        workspace_name: str,
        filename: str,
        workspace_manager: UserManager = Depends(get_user_manager),
        current_user: User = Depends(get_current_user)
) -> Any:
    try:
        workspace = await workspace_manager.get_workspace_by_name(current_user.id, workspace_name)
        await workspace_manager.create_file(filename, workspace)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    return JSONResponse(content={"message": f"File '{filename}' created successfully."}, status_code=status.HTTP_201_CREATED)

# Создание папки
@API_USER_MODULE.post(
    '/workspaces/{workspace_name}/folder', 
    summary="Create a folder in a workspace"
)
async def create_folder(
        workspace_name: str,
        foldername: str,
        workspace_manager: UserManager = Depends(get_user_manager),
        current_user: User = Depends(get_current_user)
) -> Any:
    try:
        workspace = await workspace_manager.get_workspace_by_name(current_user.id, workspace_name)
        await workspace_manager.create_folder(foldername, workspace)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    return JSONResponse(content={"message": f"Folder '{foldername}' created successfully."}, status_code=status.HTTP_201_CREATED)

@API_USER_MODULE.post(
    '/workspaces/{workspace_name}/copy', 
    summary="Copy a file or folder in a workspace"
)
async def copy_item(
        workspace_name: str,
        src: str,
        dst: str,
        workspace_manager: UserManager = Depends(get_user_manager),
        current_user: User = Depends(get_current_user)
) -> Any:
    try:
        workspace = await workspace_manager.get_workspace_by_name(current_user.id, workspace_name)
        await workspace_manager.copy_item(src, dst, workspace)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    return JSONResponse(content={"message": f"'{src}' copied to '{dst}' successfully."}, status_code=status.HTTP_200_OK)

# Удаление файла или папки
@API_USER_MODULE.delete('/workspaces/{workspace_name}/item', summary="Delete a file or folder in a workspace")
async def delete_item(
        workspace_id: str,
        path: str,
        workspace_manager: UserManager = Depends(get_user_manager),
        current_user: User = Depends(get_current_user)
) -> Any:
    try:
        workspace = await workspace_manager.get_workspace_by_name(current_user.id, workspace_id)
        await workspace_manager.delete_item(path, workspace)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    return JSONResponse(content={"message": f"'{path}' deleted successfully."}, status_code=status.HTTP_200_OK)

# Переименование файла или папки
@API_USER_MODULE.put('/workspaces/{workspace_name}/rename', summary="Rename a file or folder in a workspace")
async def rename_item(
        workspace_id: str,
        old_name: str,
        new_name: str,
        workspace_manager: UserManager = Depends(get_user_manager),
        current_user: User = Depends(get_current_user)
) -> Any:
    try:
        workspace = await workspace_manager.get_workspace_by_name(current_user.id, workspace_id)
        await workspace_manager.rename_item(old_name, new_name, workspace)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    return JSONResponse(content={"message": f"'{old_name}' renamed to '{new_name}' successfully."}, status_code=status.HTTP_200_OK)

# Редактирование файла
@API_USER_MODULE.put(
    '/workspaces/{workspace_id}/file', 
    summary="Edit a file in a workspace"
)
async def edit_file(
        workspace_name: str,
        filename: str,
        content: str,
        workspace_manager: UserManager = Depends(get_user_manager),
        current_user: User = Depends(get_current_user)
) -> Any:
    try:
        workspace = await workspace_manager.get_workspace_by_name(current_user.id, workspace_name)
        await workspace_manager.edit_file(filename, content, workspace)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    return JSONResponse(content={"message": f"File '{filename}' edited successfully."}, status_code=status.HTTP_200_OK)


@API_USER_MODULE.post(
    '/code/execute',
    summary='Testing code editor for not loging users',
)
async def execute(
    code: str = Form(...,  description="Code", min_length=1, max_length=10000),
    language: str = Form(..., description="Language", min_length=1, max_length=255),
    workspace_manager: UserManager = Depends(get_user_manager),
    current_user: User = Depends(get_current_user)
):
    response = CodeSchema(code=code, language=language)
    try:
        result = await workspace_manager.execute_user_code(response, user=current_user)
    except Exception as e :
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in code execution: {e}"
        )
    return result


@API_USER_MODULE.post(
    '/test_code_execute',
    summary='Testing code editor for not loging users',
)
async def execute(
    code: str = Form(...,  description="Code", min_length=1, max_length=10000),
    language: str = Form(..., description="Language", min_length=1, max_length=255),
    workspace_manager: UserManager = Depends(get_user_manager),
    current_user: User = Depends(get_current_user)
):
    response = CodeSchema(code=code, language=language)
    class CodeExecutor:
        USING_LANGUAGE = ['python', 'c', 'cpp', 'js', 'cs', 'go', 'ruby']

        async def test_exec(self, response, temp_files):
            """
            This method is implemented for testing code runner with temp files.
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
                output, error = self.execute_code(response.code, response.language, temp_files)
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

        def execute_code(self, code: str, language: str, temp_files: str) -> Tuple[str, Union[str, None]]:
            temp_dir = f"{os.getcwd()}/storage/temp/{temp_files}/tmp/projects"
            os.makedirs(temp_dir, exist_ok=True)
            params = {
                'language': language,
                'code': code,
                'temp_dir': temp_dir
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

        def run_docker_container(self, image: str, command: str, temp_dir: str) -> Tuple[str, Union[str, None]]:
            client = docker.from_env()
            try:
                result = client.containers.run(
                    image,
                    command,
                    volumes={os.path.abspath(temp_dir): {'bind': '/usr/src/app', 'mode': 'rw'}},
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
            temp_dir = params['temp_dir']
            path = os.path.join(temp_dir, "code.py")
            with self.create_code_file(path, code):
                container_path = "/usr/src/app/code.py"  # Путь внутри контейнера
                return self.run_docker_container("python:3.9", f"python {container_path}", temp_dir)

        def execute_c_code(self, params: dict) -> Tuple[str, Union[str, None]]:
            code = params['code']
            temp_dir = params['temp_dir']
            path = os.path.join(temp_dir, f"{str(uuid.uuid4())}.c")
            with self.create_code_file(path, code):
                container_path = "/usr/src/app/code.c"  # Путь внутри контейнера
                return self.run_docker_container("gcc:latest", f"sh -c 'gcc {container_path} -o /tmp/code && /tmp/code'", temp_dir)

        def execute_js_code(self, params: dict) -> Tuple[str, Union[str, None]]:
            code = params['code']
            temp_dir = params['temp_dir']
            path = os.path.join(temp_dir, f"{str(uuid.uuid4())}.js")
            with self.create_code_file(path, code):
                container_path = "/usr/src/app/code.js"  # Путь внутри контейнера
                return self.run_docker_container("node:latest", f"node {container_path}", temp_dir)

        def execute_cs_code(self, params: dict) -> Tuple[str, Union[str, None]]:
            code = params['code']
            temp_dir = params['temp_dir']
            path = os.path.join(temp_dir, "cs_project")
            code_file_path = os.path.join(path, f"{str(uuid.uuid4())}.cs")
            os.makedirs(path, exist_ok=True)
            with self.create_code_file(code_file_path, code):
                container_path = "/usr/src/app/cs_project"  # Путь внутри контейнера
                return self.run_docker_container(
                    "mcr.microsoft.com/dotnet/sdk:latest",
                    f"sh -c 'dotnet new console -o {container_path} --force && dotnet build {container_path} && dotnet run --project {container_path}'",
                    temp_dir
                )

        def execute_ruby_code(self, params: dict) -> Tuple[str, Union[str, None]]:
            code = params['code']
            temp_dir = params['temp_dir']
            path = os.path.join(temp_dir, f"{str(uuid.uuid4())}.rb")
            with self.create_code_file(path, code):
                container_path = "/usr/src/app/code.rb"  # Путь внутри контейнера
                return self.run_docker_container("ruby:latest", f"ruby {container_path}", temp_dir)

        def execute_golang_code(self, params: dict) -> Tuple[str, Union[str, None]]:
            code = params['code']
            temp_dir = params['temp_dir']
            path = os.path.join(temp_dir, f"{str(uuid.uuid4())}.go")
            with self.create_code_file(path, code):
                container_path = "/usr/src/app/code.go"  # Путь внутри контейнера
                return self.run_docker_container("golang:latest", f"sh -c 'go build {container_path} && {container_path}'", temp_dir)
    try:
        # result = CodeExecutor.test_exec(response, user=current_user)
        result = await workspace_manager.execute_user_code(response, user=current_user)
    except Exception as e :
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in code execution: {e}"
        )
    return result