"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""


import traceback
import logging
import logging.handlers
import sys
import os


def is_debug_set_in_environment()->bool:
    try:
        env_debug = os.getenv('DEBUG', '0').lower()
        if env_debug in ('1','true','t','enabled'):
            return True
    except:
        pass
    return False


def get_logging_stream_handler(
    level=logging.INFO,
    formatter: logging.Formatter=logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
)->logging.StreamHandler:
    try:
        h = logging.StreamHandler(sys.stdout)
        h.setLevel(level)    
        h.setFormatter(formatter)
        return h
    except:
        traceback.print_exc()
    return None


def get_logger(
    level=logging.INFO,
    log_format: str='%(asctime)s %(levelname)s - %(message)s'
)->logging.Logger:
    if is_debug_set_in_environment() is True:
        level = logging.DEBUG

    logger = logging.getLogger()
    logger.handlers = []
    formatter = logging.Formatter(log_format)

    h = get_logging_stream_handler(
        level=level,
        formatter=formatter
    )
    if h is not None:
        logger.addHandler(h)

    return logger

