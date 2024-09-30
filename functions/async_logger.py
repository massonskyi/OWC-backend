"""
Takes and modify from https://github.com/massonskyi/pyllt/blob/master/pyllt/functiontools/logger.py
Async logger for backend app
"""
import os
from typing import Union

# for alembic
# from functions.core.ensure_directory_exists import ensure_directory_exists as edx

# for main server
from functions.core.ensure_directory_exists import ensure_directory_exists as edx
from typing import Optional # noqa: F401
import asyncio
import logging
import datetime
import random
import inspect

class ColoredFormatter(logging.Formatter):
    """
    ColoredFormatter is used to format the log messages to the console and the log file.
    """
    # Define the color codes
    COLORS_TYPES = {
        'reset': '\033[0m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'cyan': '\033[96m',
        'blue': '\033[94m',
        'white': '\033[97m',
        'grey': '\033[90m',
        'magenta': '\033[95m',
        'bold': '\033[1m',
        'italic': '\033[3m',
        'underline': '\033[4m',
        'strikethrough': '\033[9m'
    }

    def format(self, record):
        """
        Formats the log message to the console and the log file.
        @param record: the log record of the log record.
        @return str: the formatted log message.
        """
        # Ensure that the asctime is included in the record
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        # Get the frame where the log message was called
        frame, filename, line_no, function_name, lines, index = inspect.stack()[7]
        class_name = frame.f_locals.get("self", None).__class__.__name__ if "self" in frame.f_locals else None
        record.pathname = filename
        record.funcName = function_name
        record.className = class_name

        # Apply colors to each part of the log message
        log_message = (
            f"[{self.COLORS_TYPES['green']}{self.COLORS_TYPES['bold']}{record.asctime}{self.COLORS_TYPES['reset']}]: "
            f"({self.COLORS_TYPES['yellow']}{record.name}{self.COLORS_TYPES['reset']} - {self.COLORS_TYPES['red']}{self.COLORS_TYPES['italic']}{class_name}{self.COLORS_TYPES['reset']}) - "
            f"{self.COLORS_TYPES['red']}{record.levelname}{self.COLORS_TYPES['reset']} - "
            f"{self.COLORS_TYPES['cyan']}{record.getMessage()}{self.COLORS_TYPES['reset']} - "
            f"{self.COLORS_TYPES['blue']}{filename}{self.COLORS_TYPES['reset']} - "
            f"{self.COLORS_TYPES['white']}{line_no}{self.COLORS_TYPES['reset']} - "
            f"{self.COLORS_TYPES['grey']}{function_name}{self.COLORS_TYPES['reset']}"
        )
        return log_message


class AsyncLogger:
    """
    Async logger for backend app 
    """
    def __init__(self, name: Union[str, None] = None):
        """
        Initialize the logger. 
        """
        edx('../logs')
        self.file_handler = logging.FileHandler(
            f'{os.getcwd()}\\logs\\{name}_{random.randint(0, 99)}_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log'
        )
        self.setup(name)
            
    def setup(self, name: Union[str, None] = None):
        """
        Setup the logger.
        @params: file_handler: the file handler of the log file. The file handler must be a file handler.
        @params: name: the name of the logger. The name must be a string.
        @return: None
        """
        if not name:
            self.name = __name__
        else:
            self.name = name

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        self.file_handler.setLevel(logging.DEBUG)

        color_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s - %(lineno)d - %(funcName)s'
        )
        plain_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s - %(lineno)d - %(funcName)s'
        )

        console_handler.setFormatter(color_formatter)
        self.file_handler.setFormatter(plain_formatter)

        # Add the handlers to the logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(self.file_handler)
    async def log(self, level: int, msg: str) -> None:
        """
        Log a message at the specified level. 
        @params: level: the level of the log message. The level must be one of the following: 
        - logging.INFO 
        - logging.WARNING 
        - logging.ERROR 
        - logging.CRITICAL
        @params: msg: the log message. The message must be a string. The message must be a string. 
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self.logger.log(level, msg))
        
    async def b_info(self, msg: str) -> None:
        """
        b_info is used to log an information message.
        @params: msg: the log message. The message must be a string. The message must be a string.
        """
        await self.log(logging.INFO, msg)
        
    async def b_warn(self, msg: str) -> None:
        """
        b_warn is used to log a warning message. 
        @params: msg: the log message. The message must be a string. The message must be a string.
        """
        await self.log(logging.WARNING, msg)

    async def b_err(self, msg: str) -> None:
        """
        b_err is used to log an error message. 
        @params: msg: the log message. The message must be a string. The message must be a string.
        """
        await self.log(logging.ERROR, msg)

    async def b_crit(self, msg: str) -> None:
        """
        b_crit is used to log a critical message.
        @params: msg: the log message. The message must be a string. The message must be a string.
        """
        await self.log(logging.CRITICAL, msg)

    async def b_exc(self, msg: str) -> None:
        """
        b_exc is used to log an exception.
        @params: msg: the log message. The message must be a string. The message must be a string.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self.logger.exception(msg))

    async def b_deb(self, msg: str) -> None:
        """
        b_deb is used to log a debug message.
        @params: msg: the log message. The message must be a string. The message must be a string.
        """
        await self.log(logging.DEBUG, msg)