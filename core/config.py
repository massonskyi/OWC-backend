"""
This file contains the configuration of the project. It will be loaded by the main script. It should not be edited
directly.

To change the configuration, edit the file in the same directory as this file. The config file is loaded by the main
script.
"""
from typing import Optional # noqa: F401
import os

__all__ = [
    'Config', 
    'load_config'
]

__version__ = '0.1.0'
__docstring__ = """ 
this is the config module of the project. 
This file is loaded by the main script. 
It should not be edited directly.
"""

from typing import List, Any
from dotenv import load_dotenv

class Config:
    """
    A class that loads the environment variables from the.env file file into the class.
    This class is used to load the environment variables. It is also used to access the environment variables.
    """
    def __init__(self, logger: object, constants_name: List[str] = None) -> None:
        """
        A class method that loads the environment variables.
        """
        load_dotenv()

        if not constants_name:
            constants_name = [
            'BACKEND_SECRET_COOKIE_KEY',
            'POSTGRES_DB',
            'POSTGRES_USER',
            'POSTGRES_PASSWORD',
            'ENVIRONMENT',
            'DB_USER',
            'DB_HOST',
            'DB_PORT',
            'DB_NAME',
            'DB_PASS',
            'DATABASE_URL'
        ]
        self.logger = logger
        self.constants = {name: None for name in constants_name}
       
    async def setup(self) -> 'Config':
        """
        A class method that sets up the environment variables.
        """
        for n in self.constants:
            env_value = os.environ.get(n)
            if env_value is not None:
                self.constants[n] = env_value
                await self.logger.b_info(f'{n} = {env_value}')
            else:
                await self.logger.b_warn(f'{n} is not set in the environment variables.')
        return self

    async def getattr(self, n: str) -> Any:
        """
        A method that returns the environment variables. It is used to access the environment variables.
        :param n: The name of the environment variable. It is used to access the environment variables.
        :return: The value of the environment variable. It is used to access the environment variables.
        :raises: AttributeError: If the environment variable is not found. It is used to access the environment variables.
        :raises: KeyError: If the environment variable is not found. It is used to access the environment variables.
        :return: The value of the environment variable. It is used to access the environment variables.
        """
        if n not in self.constants:
            await self.logger.b_crit(f'{n} is not a valid environment variable.')
            raise AttributeError(f'{n} is not a valid environment variable.')

        value = self.constants.get(n)
        if value is None:
            await self.logger.b_crit(f'{n} is not set or is None.')
            raise KeyError(f'{n} is not set or is None.')

        return value

    async def setattr(self, n: str, value: Any) -> None:
        """
        A method that sets the environment variables. It is used to set the environment variables.
        :param n: The name of the environment variable. It is used to set the environment variables.
        :param value: The value of the environment variable. It is used to set the environment variables.
        :raises: AttributeError: If the environment variable is not found. It is used to set the environment variables.
        :raises: KeyError: If the environment variable is not found. It is used to set the environment variables.
        """
        if n not in self.constants:
            await self.logger.b_crit(f'{n} is not a valid environment variable.')
            raise AttributeError(f'{n} is not a valid environment variable.')

        self.constants[n] = value
        await self.logger.b_info(f'{n} set to {value}')


async def load_config(logger, constants_name: List[str] = None) -> object:
    """
    A function that loads the environment variables.
    """
    config = Config(logger, constants_name)
    await config.setup()
    return config
