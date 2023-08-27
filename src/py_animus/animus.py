"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import json

from py_animus import parse_command_line_arguments
from py_animus.models import VariableCache, AllScopedValues

from termcolor import colored, cprint


def action_apply():
    pass


def action_delete():
    pass


ACTION_HANDLERS = {
    'apply': action_apply,
    'delete': action_delete,
}


all_scoped_values = AllScopedValues()
variable_cache = VariableCache()


def _format_line_for_print(
    text: str=None,
    text_color: str='green',
    text_blink: bool=False,
    text_reverse: bool=False,
    text_bold: bool=True
)->str:
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
    message_color: str='white',
    message_blink: bool=False,
    message_reverse: bool=False,
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
        print(
            _format_line_for_print(
                text='  Variables:',
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
        


def run_main(cli_parameter_overrides: list=list()):
    print('Nothing to do yet...')
    cli_arguments = parse_command_line_arguments(overrides=cli_parameter_overrides)
    print_console_feedback_line(
        leader='STARTING',
        leader_bold=True,
        leader_reverse=True,
        message='Animus is now running',
        variables=cli_arguments
    )

    return True


if __name__ == '__main__':
    run_main()
