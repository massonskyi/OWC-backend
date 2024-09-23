from datetime import (
    datetime, 
    timedelta
)

from typing import Any, Tuple
from jose import JWTError, jwt
from typing import Optional # noqa: F401

import os
from passlib.context import CryptContext

from fastapi import(
    Depends, 
    HTTPException,
    Request,
    status
)


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.user.models import User, UserToken

from database.session import get_async_db

from core import cfg

from middleware import (
    ALGORITHM,
    oauth2_scheme
)


class PasswordManager:
    """
    Password manager class to hash and verify passwords
    """
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

    def __init__(self) -> None:
        """
        Initialize the password manager
        """
        self.secret_key = os.urandom(32)

    def hash(self, pwd: str) -> str:
        """
        Hash the password and return the hashed password string
        """
        return self.pwd_context.hash(pwd)

    def verify(self, hashed_password: str, plain_password: str) -> bool:
        """
        Verify the hashed password with the plain password
        """
        return self.pwd_context.verify(plain_password, hashed_password)


    def is_hashed(self, password: str) -> bool:
        """
        Check if the password is hashed
        """
        # Passlib's identify method will return None if it cannot identify the hash scheme
        return self.pwd_context.identify(password) is not None
    
    
    
async def verify_token(
        request: Request,
        db: AsyncSession = Depends(get_async_db),
) -> Tuple[int, Any]:
    """
    Verify token and return user id
    :param request: Request object to get request object
    :param db: Database session object to get database session
    :return: User id from token from database session
    """
    authorization = request.headers.get("Authorization")
    if not authorization:
        cookie_token = request.cookies.get("access_token")
        if not cookie_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        token = cookie_token
    else:
        token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, cfg['BACKEND_SECRET_COOKIE_KEY'], algorithms=[ALGORITHM])
        token_data = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    token_query = await db.query(UserToken).filter(UserToken.token == token).first()
    if not token_query:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if token_query.expiration < datetime.utcnow():
        await db.delete(token_query)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired token")
    return token_query.user_id, request


def create_access_token(
        data: dict,
        expires_delta=None,
        SECRET_KEY: str = None,
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 999999,
        ALGORITHM: str = "HS256"
) -> tuple[str, datetime | Any]:
    """
    Create an access token with the given data and expiration time.

    Args:
        data: A dictionary containing the data to be encoded in the token.
        expires_delta: The expiration time for the token. If not provided, the token will expire after 30 minutes.
        SECRET_KEY: str = None,
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 30,
        ALGORITHM: str = "HS256"
    Returns:
        The encoded access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, cfg['BACKEND_SECRET_COOKIE_KEY'], algorithm=ALGORITHM)
    return encoded_jwt, expire


async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """
    Get the current user. If the token is valid, return the user.
    Args:
        token: str = Depends(oauth2_scheme), The token to validate. 
        db: AsyncSession = Depends(get_async_db) The database session.
    Returns:
        The current user. If the token is invalid, return None.
    """
    try:
        payload = jwt.decode(token, cfg['BACKEND_SECRET_COOKIE_KEY'], algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        
        if user_id is None:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: User ID is not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
            
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await db.execute(select(User).filter(User.id == user_id))
    user = user.scalars().first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: Admin not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user