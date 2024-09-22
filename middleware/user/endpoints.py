from datetime import  datetime
import json

from fastapi import (
    APIRouter, 
    Depends,
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
    tags=["Authenticate module for Online Workspace Code for you"],
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
                httponly=True,
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
        """
    finally:
        if not response_content.get('user', None):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            response_content['user'] = None
            response_content['access_token'] = None
            response_content['token_expires_at'] = None
            response_content['message'] = "User authenticated error"
        """
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
        workspace = await workspace_manager.create_workspace(current_user.id, new)
    except ValueError as val_err:
        status_code = status.HTTP_400_BAD_REQUEST
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
    '/workspaces/test_exec',
    summary='Testing code editor for not loging users',
)
async def execute(response, workspace_manager: UserManager = Depends(get_user_manager)):
    result = await workspace_manager.test_exec(response)
    if not result or result.error != '':
        raise ValueError(f"Error compilation: {result.error}")

    return result
