"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""
import os
import logging
import sys


class LoggingContext:

    def __init__(self, custom_logging_set: bool=None):
        self.custom_logging_set = False
        if custom_logging_set is not None:
            if isinstance(custom_logging_set, bool):
                self.custom_logging_set = custom_logging_set

    def enable_custom_logging(self):
        self.custom_logging_set = True


logging_context = LoggingContext(custom_logging_set=False)


log_format = '[ %(filename)s:%(funcName)s:%(lineno)d ] %(levelname)s - %(message)s'
log_level = logging.INFO
formatter = logging.Formatter(log_format)
default_handler = logging.StreamHandler(sys.stdout)
default_handler.setLevel(log_level)
default_handler.setFormatter(formatter)

logger = logging.getLogger('py-animus')


def set_global_logging_level():
    
    if logging_context.custom_logging_set is False:
        print('STARTUP: Setting Default Logging Handler: "StreamHandler"')
        logger.addHandler(default_handler)

    if os.getenv('DEBUG', '0')[0].lower() in ('1','t','e'): # 1, or [t/T]rue or [e/E]nable(d)
        print('STARTUP: Initial global logging level: DEBUG')
        logger.setLevel(logging.DEBUG)
    else:
        print('STARTUP: Initial global logging level: INFO')
        logger.setLevel(logging.INFO)


def add_handler(h):
    if logging_context.custom_logging_set is False:
        logger.handlers.clear()
        logging_context.enable_custom_logging()
    logger.addHandler(h)

