"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import copy

from py_animus import parse_command_line_arguments
from py_animus.models import variable_cache, scope, actions, Variable
from py_animus.helpers.manifest_processing import process_project
from py_animus.animus_logging import logger, set_global_logging_level
from py_animus.extensions import UnitOfWork, execution_plan

from termcolor import colored, cprint


def run_main(cli_parameter_overrides: list=list()):
    set_global_logging_level()
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

    process_project(project_manifest_uri=start_manifest, project_name=project_name)

    logger.info('Ready to rumble!')

    return True


if __name__ == '__main__':  # pragma: no cover
    run_main()
