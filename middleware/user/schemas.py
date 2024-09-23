import datetime
from typing import Optional, Union
from fastapi import File, Form, UploadFile
from pydantic import BaseModel, EmailStr, validator
import re
from typing import Optional # noqa: F401

def is_valid_password(password: str) -> bool:
    """
    Check if the password meets the complexity requirements.

    Returns:
        True if the password is valid, False otherwise.
    """
    if len(password) < 8:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.islower() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    if not any(c in '!@#$%^&*()-_=+{}[]|;:,.<>?/' for c in password):
        return False
    return True


class UserCreateSchema(BaseModel):
    """
    User Create Schema for User Creation
    """
    name: Optional[str] = Form(..., description="User name", min_length=3,  max_length=255)
    
    surname: Optional[str] = Form(..., description="Surname name",min_length=3, max_length=255)
    
    email: Optional[EmailStr]  = Form(..., description="Email address", min_length=3,  max_length=255)
    
    phone: Optional[str]  = Form(  ..., description="Phone number",min_length=3, max_length=255)
    
    age: Optional[int] = Form(..., description="Age",ge=6, le=100)
    
    username: Optional[str] = Form( ..., description="Username",min_length=3,  max_length=255)
    
    hash_password: Optional[str] = Form(..., description="Hashed password",min_length=8, max_length=255)
    avatar: Optional[UploadFile]  = File(..., description="Avatar",media_type="image/*")

    @validator('name', 'surname')
    def check_alpha_fields(cls, value: str) -> str:
        if not value.isalpha():
            raise ValueError(f"{value} must contain only alphabetic characters.")
        return value

    @validator('phone')
    def validate_phone(cls, value: str) -> str:
        phone_pattern = re.compile(r'^\+?[1-9]\d{1,14}$')
        if not phone_pattern.match(value):
            raise ValueError("Invalid phone number format.")
        return value

    @validator('hash_password')
    def validate_password(cls, value: str) -> str:
        if not is_valid_password(value):
            raise ValueError("Password does not meet complexity requirements.")
        return value

    def validate(self) -> bool:
        """
        Validate the input data.

        Returns:
            True if the data is valid, False otherwise.
        """
        try:
            self.check_alpha_fields(self.name)
            self.check_alpha_fields(self.surname)
            self.validate_phone(self.phone)
            self.validate_password(self.hash_password)
        except ValueError:
            return False
        return True
    class Config:
        from_attributes = True

class UserLoginSchema(BaseModel):
    """
    User Login Schema for User Login and Password Verification
    """
    username: Optional[str]# = Form(...,description="Username",min_length=3,max_length=255)
    password: Optional[str]# = Form( ...,description="Password",min_length=8,max_length=255)
    class Config:
        from_attributes = True

class TokenData(BaseModel):
    """
    Token Data for Storing Token Information
    """
    username: Optional[str]
    class Config:
        from_attributes = True
class Token(BaseModel):
    """
    Token Model for Storing Token Information
    """
    token: Optional[str]
    expires_in: Optional[int]  # Changed from timedelta to int for simplicity
    class Config:
        from_attributes = True

class OAuth2PasswordRequestForm(BaseModel):
    """
    OAuth2 Password Request Form
    """
    username: Optional[str]
    password: Optional[str]
    class Config:
        from_attributes = True

class UserResponseSchema(BaseModel):
    """
    User Response Schema for returning User data
    """
    id: Optional[int]
    name: Optional[str]
    surname: Optional[str]
    email: Optional[str]
    age: Optional[int]
    phone: Optional[str]
    username: Optional[str]
    avatar: Optional[str]

    class Config:
        from_attributes = True


class WorkspaceSchema(BaseModel):
    name: str
    description: Union[str, None] = None
    is_active: bool = True
    is_public: bool = True

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

class ProjectSchema(BaseModel):
    workspace_id: int
    name: str
    language: str
    description: Union[str, None] = None
    is_active: bool = True

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

class WorkspaceResponseSchema(BaseModel):
    user_id: int
    name: str
    description: Union[str, None]
    is_active: bool
    is_public: bool

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

class ProjectResponseSchema(BaseModel):
    workspace_id: int
    name: str
    language: str
    description: Union[str, None]
    is_active: bool

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
        
        
class CodeSchema(BaseModel):
    code: str
    language: str