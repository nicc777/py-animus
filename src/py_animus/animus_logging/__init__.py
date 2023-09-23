"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""
import os
import logging


logger = logging.getLogger('py-animus')


def set_global_logging_level():
    if os.getenv('DEBUG', '0')[0].lower() in ('1','t','e'): # 1, or [t/T]rue or [e/E]nable(d)
        print('STARTUP: Initial global logging level: DEBUG')
        logger.setLevel(logging.DEBUG)
    else:
        print('STARTUP: Initial global logging level: INFO')
        logger.setLevel(logging.INFO)


def add_handler(h):
    logger.addHandler(h)
