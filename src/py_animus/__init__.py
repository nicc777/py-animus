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
from datetime import datetime
from py_animus.helpers.yaml_helper import load_from_str

import yaml
try:    # pragma: no cover
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError: # pragma: no cover
    from yaml import Loader, Dumper


def get_utc_timestamp(with_decimal: bool=False): # pragma: no cover
    epoch = datetime(1970,1,1,0,0,0)
    now = datetime.utcnow()
    timestamp = (now - epoch).total_seconds()
    if with_decimal:
        return timestamp
    return int(timestamp)


def is_debug_set_in_environment()->bool:    # pragma: no cover
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
    except: # pragma: no cover
        traceback.print_exc()
    return None # pragma: no cover


def get_logger(
    level=logging.INFO,
    log_format: str='%(asctime)s %(levelname)s - %(message)s'
)->logging.Logger:
    if is_debug_set_in_environment() is True:
        level = logging.DEBUG

    logger = logging.getLogger()
    logger.setLevel(level=level)
    logger.handlers = []
    formatter = logging.Formatter(log_format)

    h = get_logging_stream_handler(
        level=level,
        formatter=formatter
    )
    if h is not None:
        logger.addHandler(h)

    logger.debug('Logging init done')
    return logger


def parse_raw_yaml_data_and_ignore_all_tags(yaml_data: str, logger=get_logger(), use_custom_parser_for_custom_tags: bool=False)->dict:
    if use_custom_parser_for_custom_tags is True:
        return load_from_str(s=yaml_data)
    configuration = dict()
    current_part = 0
    try:
        for data in yaml.load_all(yaml_data, Loader=Loader):
            current_part += 1
            configuration['part_{}'.format(current_part)] = data
    except: # pragma: no cover
        try:
            # Even though the use_custom_parser_for_custom_tags flag was False, let's try using the custom parser
            parsed_data = load_from_str(s=yaml_data)
            logger.warning('It seems the YAML contained custom tags !!! WARNING: This conversion only works ONE WAY. You will not be able to reconstruct the original YAML from the resulting dict')
            return parsed_data
        except:
            traceback.print_exc()
            raise Exception('Failed to parse configuration')
    return configuration


def validate_list(input_list: list, min_length: int=0, max_length: int=999, can_be_none: bool=False, error_message: str='List validation failed'):
    if input_list is None:
        if can_be_none is False:
            raise Exception(error_message)
    if len(input_list) < min_length or len(input_list) > max_length:
        raise Exception(error_message)


def _validate_command_line_arguments(cli_parameters:list, action_handlers: dict):
    validate_list(input_list=cli_parameters, min_length=4, max_length=4, error_message='Command line argument validation failed. Required: <<action>> <<path-to-project-yaml>> <<project-name>>')


def parse_command_line_arguments(overrides: list=list(), action_handlers: dict=dict())->tuple:
    cli_parameters = overrides
    if len(sys.argv) > 1 and len(overrides) == 0:
        cli_parameters = list(sys.argv)
    _validate_command_line_arguments(cli_parameters=cli_parameters, action_handlers=action_handlers)
    return tuple(cli_parameters)

