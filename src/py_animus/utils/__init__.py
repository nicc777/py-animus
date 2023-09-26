"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import copy
from py_animus.animus_logging import logger
from py_animus.models import variable_cache, scope, actions, Variable


def initialize_animus(cli_arguments: tuple):
    logger.info('Init Start')
    
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
    
    variable_cache.store_variable(
        variable=Variable(
            name='std::start-manifest',
            initial_value='{}'.format(start_manifest)
        ),
        overwrite_existing=True
    )

    logger.info('   Init Done')
    return start_manifest, project_name

