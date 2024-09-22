from fastapi.security import OAuth2PasswordBearer
from typing import Optional # noqa: F401
__all__ = [
    'oauth2_scheme', 
    'ALGORITHM',
    'ACCESS_TOKEN_EXPIRE_MINUTES'
]

__version__ = '1.0.0'
__doc__ ="""
A package for application admin in API server
"""
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api_version_1/user/sign_in")


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 600000

