import datetime
import os
import json
import uuid
import shutil

from sqlalchemy import (
    Column, 
    Integer,
    String, 
    ForeignKey, 
    DateTime, 
    Boolean, 
    Table,
    Text
)

from sqlalchemy.orm import validates

from middleware.user.const import DOCKER_FILES
from database.connection import Base
from database.connection import metadata


from typing import List, Optional

from middleware.user.schemas import FileResponseSchema

# metadata = MetaData()
# Define the users table
user_table = Table(
    'users',  # Table name should match the actual table name in your database
    metadata,
    
    Column(
        'id', 
        Integer,
        primary_key=True,
        autoincrement=True, 
        nullable=False,
        unique=True
    ),
    
    Column(
        'name', 
        String(255), 
        nullable=False
    ),
    
    Column(
        'surname', 
        String(255),
        nullable=False
    ),
    
    Column(
        'age', 
        Integer, 
        nullable=False
    ),
    
    Column(
        'email', 
        String(255), 
        nullable=False, 
        unique=True
    ),
    
    Column(
        'phone', 
        String(255), 
        nullable=False
    ),
    
    Column(
        'username', 
        String(255), 
        nullable=False, 
        unique=True
    ),
    
    Column(
        'hash_password',
        String(255), 
        nullable=False
    ),
    
    Column(
        'created_at',
        DateTime, 
        default=datetime.datetime.utcnow, 
        nullable=False
    ),
    
    Column(
        'updated_at',
        DateTime, 
        default=datetime.datetime.utcnow, 
        onupdate=datetime.datetime.utcnow, 
        nullable=False
    ),
    
    Column(
        'delete_at', 
        DateTime, 
        nullable=True
    ),
    
    Column(
        'last_active', 
        DateTime, 
        nullable=True
    ),
    
    Column(
        'is_active', 
        Boolean, 
        default=True, 
        nullable=False
    ),
    
    Column(
        'is_staff',
        Boolean, 
        default=False, 
        nullable=False
    ),
    
    Column(
        'is_superuser', 
        Boolean, 
        default=False, 
        nullable=False
    ),
    
    Column(
        'role', 
        String(255), 
        default='new-user', 
        nullable=False
    ),
    
    Column(
        'permissions', 
        Text, 
        default="[]", 
        nullable=False
    ),  # Changed to Text for JSON storage
    
    Column(
        'avatar', 
        String(255), 
        default='~/sp2024/mpt/DOCC/assets/default/default_avatar.jpg', 
        nullable=False
    ),
    
    Column(
        'status', 
        String(999), 
        default='new-user', 
        nullable=False
    ),
    
    Column(
        'token', 
        String(255), 
        default='', 
        nullable=False
    ),
    
    Column(
        'refresh_token', 
        String(255), 
        default='', 
        nullable=False
    ),
    
    Column(
        'uuid_file_store', 
        String(255), 
        nullable=True
    )
)

user_token_table = Table(
    'users_token',  # Ensure this name is correctly set
    metadata,
    
    Column(
        'id', 
        Integer, 
        primary_key=True, 
        autoincrement=True, 
        nullable=False, 
        unique=True
    ),
    
    Column(
        'user_id', 
        Integer, 
        ForeignKey('users.id'), 
        nullable=False
    ),  # Correct table name reference
    
    Column(
        'token',
        String, 
        unique=True
    ),
    
    Column(
        'expiration', 
        DateTime
    )
)


class User(Base):
    """
    Model for user table
    """
    __tablename__ = 'users'

    id:                         Optional[int]       =           Column(Integer, primary_key=True, index=True)
    name:                       Optional[str]       =           Column(String, index=True)
    surname:                    Optional[str]       =           Column(String)
    email:                      Optional[str]       =           Column(String, unique=True, index=True)
    phone:                      Optional[str]       =           Column(String, nullable=True)
    username:                   Optional[str]       =           Column(String, unique=True, index=True)
    hash_password:              Optional[str]       =           Column(String)
    age:                        Optional[int]       =           Column(Integer, default=0, nullable=False)
    created_at:                 Optional[DateTime]  =           Column(DateTime, default=datetime.datetime.utcnow)
    updated_at:                 Optional[DateTime]  =           Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    delete_at:                  Optional[DateTime]  =           Column(DateTime, nullable=True)
    last_active:                Optional[DateTime]  =           Column(DateTime, nullable=True)
    is_active:                  Optional[Boolean]   =           Column(Boolean, default=True)
    is_staff:                   Optional[Boolean]   =           Column(Boolean, default=False)
    is_superuser:               Optional[Boolean]   =           Column(Boolean, default=False)
    role:                       Optional[str]       =           Column(String, default="user")
    permissions:                Optional[str]       =           Column(Text, default="[]")  # Ensure this is Text for JSON
    avatar:                     Optional[str]       =           Column(String, nullable=True)
    status:                     Optional[str]       =           Column(String, default="")
    token:                      Optional[str]       =           Column(String, nullable=True)
    refresh_token:              Optional[str]       =           Column(String, nullable=True)
    uuid_file_store:            Optional[str]       =           Column(String(255), nullable=True)

    def __init__(
        self,
        name:                  Optional[str]        =           None,
        surname:               Optional[str]        =           None,
        email:                 Optional[str]        =           None,
        phone:                 Optional[str]        =           None,
        username:              Optional[str]        =           None,
        hash_password:         Optional[str]        =           None,
        age:                   Optional[int]        =           None,
        created_at:            Optional[DateTime]   =           None,
        updated_at:            Optional[DateTime]   =           None,
        delete_at:             Optional[DateTime]   =           None,
        last_active:           Optional[DateTime]   =           None,
        is_active:             Optional[Boolean]    =           None,
        is_staff:              Optional[Boolean]    =           None,
        is_superuser:          Optional[Boolean]    =           None,
        role:                  Optional[str]        =           None,
        permissions:           Optional[str]        =           None,
        avatar:                Optional[str]        =           None,
        status:                Optional[str]        =           None,
        token:                 Optional[str]        =           None,
        refresh_token:         Optional[str]        =           None,
    ) -> None:
        """
        Initialize the class instance
        Args:
            name:                  Optional[str]        =       None,
            surname:               Optional[str]        =       None,
            email:                 Optional[str]        =       None,
            phone:                 Optional[str]        =       None,
            username:              Optional[str]        =       None,
            hash_password:         Optional[str]        =       None,
            age:                   Optional[int]        =       None,
            created_at:            Optional[DateTime]   =       None,
            updated_at:            Optional[DateTime]   =       None,
            delete_at:             Optional[DateTime]   =       None,
            last_active:           Optional[DateTime]   =       None,
            is_active:             Optional[Boolean]    =       None,
            is_staff:              Optional[Boolean]    =       None,
            is_superuser:          Optional[Boolean]    =       None,
            role:                  Optional[str]        =       None,
            permissions:           Optional[str]        =       None,
            avatar:                Optional[str]        =       None,
            status:                Optional[str]        =       None,
            token:                 Optional[str]        =       None,
            refresh_token:         Optional[str]        =       None,
        Return:
            None
            
        Raises: 
            ValueError: If the name is not a string or None
        """
        self.name=name
        self.surname=surname
        self.email=email
        self.phone=phone
        self.username=username
        self.hash_password=hash_password
        self.age=age
        self.created_at=created_at
        self.updated_at=updated_at
        self.delete_at=delete_at
        self.last_active=last_active
        self.is_active=is_active
        self.is_staff=is_staff
        self.is_superuser=is_superuser
        self.role=role
        self.permissions=permissions
        self.avatar=avatar
        self.status=status
        self.token=token
        self.refresh_token=refresh_token
        
        # Create the user object workspace files
        self.create_user_workspace_files()
    @validates('name', 'surname')
    def validate_names(self, key, value):
        """
        Validates that the name is only letters
        """
        if not isinstance(value, str):
            raise ValueError(f'{key.capitalize()} must be a string')
        if not value.isalpha():
            raise ValueError(f'{key.capitalize()} must only contain letters')
        return value

    @validates('username')
    def validate_username(self, key, value):
        """
        Validates that the username is only letters
        """
        if not isinstance(value, str):
            raise ValueError('Username must be a string')
        if len(value) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if ' ' in value:
            raise ValueError('Username cannot contain spaces')
        return value
    

    def __iter__(self):
        """
        Overriding the __iter__ method
        """
        for attr, value in self.__dict__.items():
            if not attr.startswith('_'):
                yield attr, value

    def to_dict(self):
        """
        Convert object to dictionary
        """
        data = {}
        for attr, value in self:
            if isinstance(value, datetime.datetime):
                data[attr] = value.isoformat()  # Convert datetime to ISO format string
            else:
                data[attr] = value
        return data

    def set_new_token(self, token: str) -> bool:
        """
        Set new token for user and return True if token is valid, False otherwise 
        """
        if not token or not isinstance(token, str):
            return False
        self.token = token
        return True
    
    def set_new_refresh_token(self, token: str) -> bool:
        """
        Set new refresh token for user and return True if token is valid, False otherwise 
        """
        if not token or not isinstance(token, str):
            return False
        self.refresh_token = token
        return True
    
    def create_user_workspace_files(
        self,
        ):
        """
        Create user workspace files in storage folder and add records to the database
        """
        self.uuid_file_store = str(uuid.uuid4())[:8]  # Создание случайного UUID для файла

        # Создание основной папки для пользователя
        user_folder = os.path.join('storage', f'{self.username}_{self.uuid_file_store}')
        os.makedirs(user_folder, exist_ok=True)

        # Создание подпапок
        subfolders = ['dockers', 'tmp', 'avatar']
        for folder in subfolders:
            os.makedirs(os.path.join(user_folder, folder), exist_ok=True)

        # Создание JSON файла
        user_info = {
            'id': self.id,
            'name': self.name,
            'surname': self.surname,
            'email': self.email,
            'phone': self.phone,
            'username': self.username,
            'hash_password': self.hash_password,
            'age': self.age,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'delete_at': self.delete_at.isoformat() if self.delete_at else None,
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'is_active': self.is_active,
            'is_staff': self.is_staff,
            'is_superuser': self.is_superuser,
            'role': self.role,
            'permissions': self.permissions,
            'avatar': self.avatar,
            'status': self.status,
            'token': self.token,
            'refresh_token': self.refresh_token,
            'uuid_file_store': self.uuid_file_store
        }
        with open(os.path.join(user_folder, 'user-info.json'), 'w') as json_file:
            json.dump(user_info, json_file)

        # Создание TXT файла
        with open(os.path.join(user_folder, 'user-info.txt'), 'w') as txt_file:
            txt_file.write(f'ID: {self.id}\n')
            txt_file.write(f'Name: {self.name}\n')
            txt_file.write(f'Surname: {self.surname}\n')
            txt_file.write(f'Email: {self.email}\n')
            txt_file.write(f'Phone: {self.phone}\n')
            txt_file.write(f'Username: {self.username}\n')
            txt_file.write(f'Hash Password: {self.hash_password}\n')
            txt_file.write(f'Age: {self.age}\n')
            txt_file.write(f'Created At: {self.created_at.isoformat() if self.created_at else None}\n')
            txt_file.write(f'Updated At: {self.updated_at.isoformat() if self.updated_at else None}\n')
            txt_file.write(f'Delete At: {self.delete_at.isoformat() if self.delete_at else None}\n')
            txt_file.write(f'Last Active: {self.last_active.isoformat() if self.last_active else None}\n')
            txt_file.write(f'Is Active: {self.is_active}\n')
            txt_file.write(f'Is Staff: {self.is_staff}\n')
            txt_file.write(f'Is Superuser: {self.is_superuser}\n')
            txt_file.write(f'Role: {self.role}\n')
            txt_file.write(f'Permissions: {self.permissions}\n')
            txt_file.write(f'Avatar: {self.avatar}\n')
            txt_file.write(f'Status: {self.status}\n')
            txt_file.write(f'Token: {self.token}\n')
            txt_file.write(f'Refresh Token: {self.refresh_token}\n')
            txt_file.write(f'UUID File Store: {self.uuid_file_store}\n')

        # Загрузка изображения (если есть)
        if self.avatar:
            avatar_folder = os.path.join(user_folder, 'avatar')
            image_path = os.path.join(avatar_folder, os.path.basename(self.avatar))

            if self.avatar.startswith('http://') or self.avatar.startswith('https://'):
                # Если ссылка не содержит в себе типа изображения,
                # то конвертируем его автоматически в .jpg
                if not self.avatar.endswith('.jpg') and \
                not self.avatar.endswith('.jpeg') and \
                not self.avatar.endswith('.png'):
                    image_path += '.jpg'
            else:
                # Копирование изображения из локальной файловой системы
                shutil.copy(self.avatar, image_path)

            # Сохранение ссылки на изображение в базе данных
            self.avatar = image_path
        for language, dockerfile_content in DOCKER_FILES.items():
            language_folder = os.path.join(user_folder, 'dockers', language)
            os.makedirs(language_folder, exist_ok=True)
            with open(os.path.join(language_folder, 'Dockerfile'), 'w') as dockerfile:
                dockerfile.write(dockerfile_content)


    def create_workspace(
        self
    ) -> 'Workspace':
        """
        Create workspace for user with user_id
        Args:
            user_id: int, ID пользователя
        """
        # Создание записи в таблице workspaces
        assert isinstance(self.id, int), 'user_id must be int'
        assert self.id > 0, 'user_id must be greater than 0'

        return Workspace(
            user_id=self.id,
            name=f'{self.username}_{self.uuid_file_store}',
            description=f'Workspace for {self.username}',
            is_active=True,
            uuid_workspace=self.uuid_file_store,
            filepath=os.path.join('storage', f'{self.username}_{self.uuid_file_store}')
        )
    

class UserToken(Base):
    __tablename__ = 'users_token'
    
    id:                 Optional[int]   =   Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    user_id:            Optional[int]   =   Column(Integer, ForeignKey('users.id'), nullable=False)  # Correct table name reference
    token:              Optional[str]   =   Column(String, unique=True)
    expiration:         Optional[DateTime]   =   Column(DateTime)


# Define the workspaces table
import datetime
from typing import Optional

from sqlalchemy import Table, Column, Integer, ForeignKey, String, DateTime, Boolean

from database.connection import metadata, Base

workspace_table = Table(
    'workspaces',
    metadata,
    Column(
        'id',
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        unique=True
    ),
    Column(
        'user_id',
        Integer,
        ForeignKey('users.id'),
        nullable=False
    ),
    Column(
        'name',
        String(255),
        nullable=False
    ),
    Column(
        'description',
        String(1024),
        nullable=True
    ),
    Column(
        'created_at',
        DateTime,
        default=datetime.datetime.utcnow,
        nullable=False
    ),
    Column(
        'updated_at',
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False
    ),
    Column(
        'is_active',
        Boolean,
        default=True,
        nullable=False
    ),
    Column(
        'is_public',
        Boolean,
        default=True,
        nullable=False
    ),
    Column(
        'filepath',
        String(255),
        nullable=True
    ),
    Column(
        'uuid_workspace',
        String(255),
        nullable=True
    )
)



class Workspace(Base):
    __tablename__ = 'workspaces'

    id: Optional[int] = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        unique=True
    )

    user_id: Optional[int] = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=False
    )

    name: Optional[str] = Column(
        String(255),
        nullable=False
    )

    description: Optional[str] = Column(
        String(1024),
        nullable=True
    )

    created_at: Optional[DateTime] = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        nullable=False
    )

    updated_at: Optional[DateTime] = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False
    )

    is_active: Optional[bool] = Column(
        Boolean,
        default=True,
        nullable=False
    )

    is_public: Optional[bool] = Column(
        Boolean,
        default=True,
        nullable=False
    )
    
    filepath: Optional[str] = Column(
        String(255),
        nullable=True
    )
    uuid_workspace: Optional[str] = Column(
        String(255),
        nullable=True
    )
    def __iter__(self):
        """
        Overriding the __iter__ method
        """
        for attr, value in self.__dict__.items():
            if not attr.startswith('_'):
                yield attr, value

    def to_dict(self):
        """
        Convert object to dictionary
        """
        data = {}
        for attr, value in self:
            if isinstance(value, datetime.datetime):
                data[attr] = value.isoformat()  # Convert datetime to ISO format string
            else:
                data[attr] = value
        return data

    def create_workspace(self, user: User):
        workspace_uuid = str(uuid.uuid4())
        server_dir = os.getcwd()
        base_dir = os.path.join(server_dir, 'storage', f'{user.username}_{user.uuid_file_store}')
        workspace_dir = os.path.join(base_dir, f'{self.name}_{workspace_uuid}')
       
        self.filepath = workspace_dir
        self.uuid_workspace = workspace_uuid
        
        os.makedirs(workspace_dir, exist_ok=True)
        
        # # Создаем структуру папок
        # os.makedirs(os.path.join(workspace_dir, "temp"), exist_ok=True)
        # os.makedirs(os.path.join(workspace_dir, "projects"), exist_ok=True)
        # os.makedirs(os.path.join(workspace_dir, "assets"), exist_ok=True)
        
        # # Создаем JSON файл с данными о пользователе
        # user_json_path = os.path.join(workspace_dir, "user_data.json")
        # with open(user_json_path, 'w') as json_file:
        #     json.dump(user.to_dict(), json_file, indent=4)
        
        # # Создаем TXT файл с данными о пользователе
        # user_txt_path = os.path.join(workspace_dir, "user_data.txt")
        # with open(user_txt_path, 'w') as txt_file:
        #     for key, value in user.to_dict().items():
        #         txt_file.write(f"{key}: {value}\n")
        
        print(f"Workspace создан в {workspace_dir}")

    def delete_workspace(self):
        # Удаляем папку с файлами
        shutil.rmtree(self.filepath)
        return True

    def get_file_list(self) -> list:
        # Получаем список файлов и папок в папке
        file_list = os.listdir(self.filepath)
        return file_list

    def get_file_path(self, file_name: str) -> str:
        # Получаем полный путь к файлу
        return os.path.join(self.filepath, file_name)
    def create_folder(self, folder) -> bool:
        
        os.mkdir(folder)
        return True

    def create_file(self, file) -> bool:

        with open(file, 'w') as f:
            f.write('')
            
        return True
    
    def copy(self, src: str, dst: str) -> bool:
   
        
        if os.path.exists(src):
            try:
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
                return True
            except Exception as e:
                print(f"Ошибка копирования: {e}")
                return False
        return False

    # Функция для удаления файла или папки
    def delete(self, path: str) -> bool:
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                return True
            except Exception as e:
                print(f"Ошибка удаления: {e}")
                return False
        return False

    # Функция для редактирования (переименования) файла или папки
    def rename(self, old_name: str, new_name: str) -> bool:
        if os.path.exists(old_name):
            try:
                os.rename(old_name, new_name)
                return True
            except Exception as e:
                print(f"Ошибка переименования: {e}")
                return False
        return False

    # Функция для изменения содержимого файла
    def edit_file(self, file: str, content: str) -> bool:
        
        if os.path.exists(file) and os.path.isfile(file):
            try:
                with open(file, 'w') as f:
                    f.write(content)
                return True
            except Exception as e:
                print(f"Ошибка редактирования файла: {e}")
                return False
        return False
    
    def open_file(self, file: str) -> str:
        if not os.path.exists(file):
            raise ValueError(f"File {file} does not exist")
        
        with open(file, 'r') as f:
            return f.read()
        
    def get_all_files_and_dirs(self):
        """
        Get all files and directories in the workspace.
        Returns a structured result containing files and directories recursively.
        """
        
        def get_dir_contents(path):
            contents = []
            for entry in os.listdir(path):
                entry_path = os.path.join(path, entry)
                if os.path.isdir(entry_path):
                    # Recursively get children for directories
                    children = get_dir_contents(entry_path)
                    contents.append(FileResponseSchema(
                        name=entry,
                        type="folder",
                        children=children
                    ))
                else:
                    # Get file size for files
                    file_size = os.path.getsize(entry_path)
                    contents.append(FileResponseSchema(
                        name=entry,
                        type="file",
                        size=file_size
                    ))
            return contents

        try:
            base_dir = self.filepath
            if not os.path.exists(base_dir):
                return {"error": "Workspace directory does not exist"}

            result = get_dir_contents(base_dir)  # Call the recursive function
            
        except Exception as e:
            # Print the exception message to help debugging
            print(f"Error getting files and directories: {e}")
            raise ValueError(f"Error getting files and directories: {e}")

        return result  # Return a list of FileResponseSchema