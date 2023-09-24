"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""


import traceback
import sys


SUPPORTED_COMMANDS = (
    'apply',
    'delete',
)


def get_logging_stream_handler(
    level,
    formatter=None
):
    import logging
    if formatter is None:
        formatter: logging.Formatter=logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
    try:
        h = logging.StreamHandler(sys.stdout)
        h.setLevel(level)    
        h.setFormatter(formatter)
        return h
    except: # pragma: no cover
        traceback.print_exc()
    return None # pragma: no cover


def validate_list(input_list: list, min_length: int=0, max_length: int=999, can_be_none: bool=False, error_message: str='List validation failed'):
    if input_list is None:
        if can_be_none is False:
            raise Exception(error_message)
    if input_list is not None:
        if isinstance(input_list, list) is False:
            raise Exception(error_message)
        if len(input_list) < min_length or len(input_list) > max_length:
            raise Exception(error_message)


def validate_string_value(input_string: str, can_be_none: bool=False, can_be_empty: str=True, min_length: int=0, max_length: int=1024, error_message: str='List validation failed'):
    if can_be_none is False:
        if input_string is None:
            raise Exception(error_message)
    if input_string is not None:
        if len(input_string) == 0 and can_be_empty is False:
            raise Exception(error_message)
        if len(input_string) < min_length or len(input_string) > max_length:
            raise Exception(error_message)


def validate_word_in_list_of_possible_values(input_string: str, possible_values: list=list(), error_message: str='The input string did not match any of the required values'):
    if input_string not in possible_values:
        raise Exception(error_message)


def _validate_command_line_arguments(cli_parameters:list):
    validate_list(input_list=cli_parameters, min_length=5, max_length=5, error_message='Command line argument validation failed. Required: <<action>> <<path-to-project-manifest>> <<project-name>> <<environment-or-scope>>')
    for param in cli_parameters[1:]:
        validate_string_value(input_string=param, can_be_empty=False, min_length=3, max_length=1024, error_message='Every command line argument must be a valid string: <<action>> <<path-to-project-yaml>> <<project-name>>')
    validate_word_in_list_of_possible_values(input_string=cli_parameters[1], possible_values=SUPPORTED_COMMANDS, error_message='action parameter must be one of: {}'.format(SUPPORTED_COMMANDS))


def parse_command_line_arguments(overrides: list=list())->tuple:
    cli_parameters = overrides
    if len(sys.argv) > 1 and len(overrides) == 0:
        cli_parameters = list(sys.argv)
    _validate_command_line_arguments(cli_parameters=cli_parameters)
    return tuple(cli_parameters)

