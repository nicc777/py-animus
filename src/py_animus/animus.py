"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import json
import copy

from py_animus import parse_command_line_arguments
from py_animus.models import all_scoped_values, variable_cache, scope, ScopedValues, Value, actions, Variable
from py_animus.helpers.file_io import file_exists, read_text_file
from py_animus.helpers.yaml_helper import spit_yaml_text_from_file_with_multiple_yaml_sections, load_from_str_and_ignore_custom_tags, parse_animus_formatted_yaml
from py_animus.helpers.manifest_processing import read_manifest_and_extract_individual_yaml_sections, parse_project_manifest_items, process_selected_project
from py_animus.utils.http_requests_io import download_files
from py_animus.animus_logging import logger
from py_animus.extensions import UnitOfWork, execution_plan

from termcolor import colored, cprint


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



def run_main(cli_parameter_overrides: list=list()):
    print('Nothing to do yet...')
    cli_arguments = parse_command_line_arguments(overrides=cli_parameter_overrides)

    actions.set_command(command='{}'.format(cli_arguments[1]))
    start_manifest = cli_arguments[2]
    project_name = cli_arguments[3]
    scope.set_scope(new_value=cli_arguments[4])

    variable_cache.store_variable(
        variable=Variable(
            name='std::action',
            initial_value='{}'.format(copy.deepcopy(actions.command))
        ),
        overwrite_existing=True
    )

    variable_cache.store_variable(
        variable=Variable(
            name='std::project-name',
            initial_value='{}'.format(project_name)
        ),
        overwrite_existing=True
    )

    print_console_feedback_line(
        leader='STARTING: ',
        leader_bold=True,
        leader_reverse=True,
        message='Animus is now running',
        variables_heading_text='  Command Line Arguments:',
        variables=[cli_arguments,]
    )
    
    if start_manifest.lower().startswith('http'):
        files = download_files(urls=[start_manifest,])
        if len(files) > 0:
            start_manifest = files[0]

    if file_exists(start_manifest) is False:
        raise Exception('Manifest file "{}" does not exist!'.format(start_manifest))
    
    variable_cache.store_variable(
        variable=Variable(
            name='std::start-manifest',
            initial_value='{}'.format(start_manifest)
        ),
        overwrite_existing=True
    )

    yaml_sections = read_manifest_and_extract_individual_yaml_sections(start_manifest=start_manifest, process_logging=False, process_values=False)
    logger.info('Initial yaml_sections calculated: {} section(s)'.format(len(yaml_sections)))
    
    variable_cache.store_variable(
        variable=Variable(
            name='std::all-yaml-sections',
            initial_value=yaml_sections
        ),
        overwrite_existing=True
    )

    process_selected_project()

    # yaml_sections = parse_project_manifest_items(yaml_sections=yaml_sections, project_name=project_name)

    logger.info('Ready to rumble!')

    return True


if __name__ == '__main__':  # pragma: no cover
    run_main()
