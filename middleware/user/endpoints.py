from datetime import  datetime
import json

from fastapi import (
    APIRouter, 
    Depends,
    Form,
    HTTPException, 
    status,
    Response

)
from fastapi.security import OAuth2PasswordRequestForm


from sqlalchemy.ext.asyncio import AsyncSession


from database.session import get_async_db


from middleware.user.manager import UserManager
from middleware.user.models import User

from middleware.user.schemas import (
    CodeSchema,
    ProjectSchema,
    UserCreateSchema,
    Token,
    UserLoginSchema, WorkspaceSchema
)
from typing import Optional # noqa: F401

from middleware.utils import get_current_user

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
        response_content['access_token'] = access_token
        response_content['token_expires_at'] = expire.timestamp()
        response_content['message'] = "User created successfully"
        status_code = status.HTTP_201_CREATED
    finally:
        
        if not response_content.get('user', None):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            response_content['user'] = None
            response_content['access_token'] = None
            response_content['token_expires_at'] = None
            response_content['message'] = "User created error"

        response_json = json.dumps(response_content)
        response = Response(content=response_json, media_type="application/json", status_code=status_code)

        if access_token and expire:
            # Set the cookie
            response.set_cookie(
                key="access_token",
                value=access_token ,
                expires=expire.timestamp(),
                secure=False,
                httponly=False,
                samesite=None,
                path="/",
                domain="localhost"
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
        user, access_token, expire = await user_manager.authenticate_user(form_data.username, form_data.password)
        if not access_token or not user:
            status_code = status.HTTP_400_BAD_REQUEST
            raise HTTPException(
                status_code=status_code, 
                detail="Incorrect email or password"
            )
        expire = expire.timestamp()
    except Exception as e:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(
            status_code=status_code, 
            detail=str(e)
        )
        
    else:
        response_content['user'] = user.to_dict()
        response_content['access_token'] = access_token
        response_content['token_expires_at'] = expire
        response_content['message'] = "User authenticated successfully"
        status_code = status.HTTP_200_OK
        
    finally:
        if not response_content.get('user', None):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            response_content['user'] = None
            response_content['access_token'] = None
            response_content['token_expires_at'] = None
            response_content['message'] = "User authenticated error"
            
        response_json = json.dumps(response_content)  # Convert dictionary to JSON string
        response = Response(content=response_json, media_type="application/json", status_code=status_code)

        if access_token and expire:
            response.set_cookie(
                key="access_token",
                value=access_token,
                expires=expire,  # Convert datetime to timestamp
                secure=False,  # Optional: Set Secure flag if using HTTPS
                httponly=True,  # Optional: Set the HttpOnly flag for security
                samesite=None, # Optional: Set SameSite policy
                path="/",  # Ensure the cookie is available throughout your site
                domain="localhost"  # Adjust this if your site spans multiple subdomains
            )
        return response



@API_USER_MODULE.post(
    '/workspaces',
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
    '/workspaces/{workspace_id}',
    summary="Delete workspace by ID",
)
async def delete_workspace(
        workspace_id: int,
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
    '/projects/',
    summary="Create a new project",
)
async def create_project(
        workspace_id: int,
        new: ProjectSchema = Depends(),
        project_manager: UserManager = Depends(get_user_manager),
        current_user: User = Depends(get_current_user)
) -> Response:
    status_code = None
    response_content = {}
    try:
        new.workspace_id = workspace_id 
        project = await project_manager.create_project(current_user, new)
    except Exception as e:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )
    else:
        response_content['project'] = project.dict()
        response_content['message'] = "Project created successfully"
        status_code = status.HTTP_201_CREATED
    finally:
        response_json = json.dumps(response_content)
        return Response(content=response_json, media_type="application/json", status_code=status_code)

@API_USER_MODULE.get(
    '/projects/{project_id}',
    summary="Get project by ID",
)
async def get_project(
        workspace_id: int,
        project_id: Optional[int],
        project_manager: UserManager = Depends(get_user_manager),
        current_user: User = Depends(get_current_user)
) -> Response:
    """
    Retrieve a project by its ID for the user.
    """
    status_code = None
    response_content = {}
    if project_id is None:
        status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
            detail="Project ID is not found"
        )
    try:
        project = await project_manager.get_project(workspace_id, project_id)
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
        response_content['project'] = project.dict()
        response_content['message'] = "Project retrieved successfully"
        status_code = status.HTTP_200_OK
    finally:
        response_json = json.dumps(response_content)
        return Response(content=response_json, media_type="application/json", status_code=status_code)

@API_USER_MODULE.get(
    '/projects/',
    summary="Get all projects for the user",
)
async def get_projects(
        workspace_id: int,
        project_manager: UserManager = Depends(get_user_manager),
        current_user: User = Depends(get_current_user)
) -> Response:
    """
    Retrieve all projects for the user.
    """
    status_code = None
    response_content = {}
    try:
        projects = await project_manager.get_projects(workspace_id)
    except Exception as e:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )
    else:
        response_content['projects'] = [proj.dict() for proj in projects]
        response_content['message'] = "Projects retrieved successfully"
        status_code = status.HTTP_200_OK
    finally:
        response_json = json.dumps(response_content)
        return Response(content=response_json, media_type="application/json", status_code=status_code)

@API_USER_MODULE.delete(
    '/projects/{project_id}',
    summary="Delete project by ID",
)
async def delete_project(
        workspace_id: int,
        project_id: int,
        project_manager: UserManager = Depends(get_user_manager),
        current_user: User = Depends(get_current_user)
) -> Response:
    """
    Delete a project by its ID for the user.
    """
    status_code = None
    response_content = {}
    try:
        await project_manager.delete_project(workspace_id, project_id)
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
        response_content['message'] = "Project deleted successfully"
        status_code = status.HTTP_200_OK
    finally:
        response_json = json.dumps(response_content)
        return Response(content=response_json, media_type="application/json", status_code=status_code)

@API_USER_MODULE.put(
    '/projects/{project_id}',
    summary="Update project by ID",
)
async def update_project(
        workspace_id: int,
        project_id: int,
        updated_data: ProjectSchema = Depends(),
        project_manager: UserManager = Depends(get_user_manager),
        current_user: User = Depends(get_current_user)
) -> Response:
    """
    Update a project by its ID for the user.
    """
    status_code = None
    response_content = {}
    try:
        updated_data.workspace_id = workspace_id  # Устанавливаем workspace_id для проекта
        project = await project_manager.update_project(current_user.id, project_id, updated_data)
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
        response_content['project'] = project.dict()
        response_content['message'] = "Project updated successfully"
        status_code = status.HTTP_200_OK
    finally:
        response_json = json.dumps(response_content)
        return Response(content=response_json, media_type="application/json", status_code=status_code)
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
        result = await workspace_manager.test_exec(response, user=current_user)
    except Exception as e :
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in code execution: {e}"
        )
    return result
