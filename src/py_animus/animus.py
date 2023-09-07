"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import json

from py_animus import parse_command_line_arguments
from py_animus.models import all_scoped_values, variable_cache, scope, ScopedValues, Value, actions
from py_animus.helpers.file_io import file_exists, read_text_file
from py_animus.helpers.yaml_helper import spit_yaml_text_from_file_with_multiple_yaml_sections, load_from_str_and_ignore_custom_tags, parse_animus_formatted_yaml
from py_animus.utils.http_requests_io import download_files
from py_animus.extensions.stream_handler_logging_v1 import StreamHandlerLogging
from py_animus.extensions.file_handler_logging_v1 import FileHandlerLogging
from py_animus.animus_logging import logger

from termcolor import colored, cprint


def action_apply():
    pass


def action_delete():
    pass


ACTION_HANDLERS = {
    'apply': action_apply,
    'delete': action_delete,
}


def _format_line_for_print( 
    text: str=None,
    text_color: str='green',
    text_blink: bool=False,
    text_reverse: bool=False,
    text_bold: bool=True
)->str: # pragma: no cover
    attrs = list()
    if text_blink is True:
        attrs.append('blink')
    if text_reverse is True:
        attrs.append('reverse')
    if text_bold is True:
        attrs.append('bold')
    return colored('{} '.format(text), text_color, attrs=attrs)


def print_console_feedback_line(
    leader: str=None,
    leader_color: str='green',
    leader_blink: bool=False,
    leader_reverse: bool=False,
    leader_bold: bool=True,
    message: str='',
    message_color: str='green',
    message_blink: bool=False,
    message_reverse: bool=False,
    variables_heading_text: str='  Variables:',
    variables: list=list(),
    variable_color: str='blue',
    variable_reverse: bool=False
):
    final_leader_text = ''
    if leader is not None:
        final_leader_text = _format_line_for_print(
            text=leader,
            text_color=leader_color,
            text_blink=leader_blink,
            text_reverse=leader_reverse,
            text_bold=leader_bold
        )
    print(
        final_leader_text,
        _format_line_for_print(
            text=message,
            text_color=message_color,
            text_blink=message_blink,
            text_reverse=message_reverse
        )
    )
    if len(variables) > 0:
        print()
        print(
            _format_line_for_print(
                text='{}'.format(variables_heading_text),
                text_color='white',
                text_reverse=True
            )
        )
        print()
    for variable in variables:
        variable_text = '{}'.format(variable)
        if isinstance(variable, dict) is True or isinstance(variable, list) is True or isinstance(variable, tuple):
            variable_text = json.dumps(variable, default=str)
        print(
            '    {}'.format(
                _format_line_for_print(
                    text=variable_text,
                    text_color=variable_color,
                    text_reverse=variable_reverse
                )
            )
        )
    print()
    print()


def _parse_values_data(manifest_data: dict):
    converted_data = dict((k.lower(),v) for k,v in manifest_data.items()) # Convert keys to lowercase
    scoped_values = ScopedValues(scope=scope.value)
    if 'kind' in converted_data:
        if converted_data['kind'] == 'Values':
            if 'spec' in converted_data:
                if 'values' in converted_data['spec']:
                    for value_data in converted_data['spec']['values']:
                        if 'valueName' in value_data:
                            value_name = value_data['valueName']
                            final_value = None
                            if 'defaultValue' in value_data:
                                final_value = value_data['defaultValue']
                            if 'environmentOverrides' in value_data:
                                for override_data in value_data['environmentOverrides']:
                                    if 'environmentName' in override_data and 'value' in override_data:
                                        if override_data['environmentName'] == scope.value:
                                            final_value = override_data['value']
                            scoped_values.add_value(
                                value=Value(
                                    name=value_name,
                                    initial_value=final_value
                                )
                            )
    all_scoped_values.add_scoped_values(scoped_values=scoped_values)


def step_read_project_manifest(start_manifest: str):
    print_console_feedback_line(
        leader='STEP: ',
        leader_bold=True,
        leader_reverse=True,
        message='Reading project manifest: {}'.format(start_manifest),
    )
    start_manifest_yaml_sections = spit_yaml_text_from_file_with_multiple_yaml_sections(yaml_text=start_manifest)
    if 'Values' in start_manifest_yaml_sections:
        for value_manifest_section_text in start_manifest_yaml_sections['Values']:
            _parse_values_data(manifest_data=load_from_str_and_ignore_custom_tags(value_manifest_section_text)['part_1'])
    logging_actions = list()
    for logging_kind in ('StreamHandlerLogging', 'FileHandlerLogging',):
        if logging_kind in start_manifest_yaml_sections:
            for value_manifest_section_text in start_manifest_yaml_sections[logging_kind]:
                stream_logging_instance = parse_animus_formatted_yaml(raw_yaml_str=value_manifest_section_text)
                stream_logging_instance.determine_actions()
                logging_actions.append(stream_logging_instance)
    for logging_extension in logging_actions:
        logging_extension.apply_manifest()
    logger.info('Logging ready')


def run_main(cli_parameter_overrides: list=list()):
    print('Nothing to do yet...')
    cli_arguments = parse_command_line_arguments(overrides=cli_parameter_overrides, action_handlers=ACTION_HANDLERS)
    print_console_feedback_line(
        leader='STARTING: ',
        leader_bold=True,
        leader_reverse=True,
        message='Animus is now running',
        variables_heading_text='  Command Line Arguments:',
        variables=[cli_arguments,]
    )
    actions.set_command(command='{}'.format(cli_arguments[1]))
    start_manifest = cli_arguments[2]
    project_name = cli_arguments[3]
    scope.set_scope(new_value=cli_arguments[4])

    if start_manifest.lower().startswith('http'):
        files = download_files(urls=[start_manifest,])
        if len(files) > 0:
            start_manifest = files[0]

    if file_exists(start_manifest) is False:
        raise Exception('Manifest file "{}" does not exist!'.format(start_manifest))

    step_read_project_manifest(start_manifest=start_manifest)

    return True


if __name__ == '__main__':  # pragma: no cover
    run_main()
