"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

from py_animus.animus_logging import logger, set_global_logging_level
from py_animus import parse_command_line_arguments


def run_main(cli_parameter_overrides: list=list()):
    set_global_logging_level()
    logger.info('Starting')
    cli_arguments = parse_command_line_arguments(overrides=cli_parameter_overrides)

    from py_animus.utils import initialize_animus
    start_manifest, project_name = initialize_animus(cli_arguments=cli_arguments)

    from py_animus.helpers.manifest_processing import process_project, tracker
    tracker.reset()
    process_project(
        project_manifest_uri=start_manifest,
        project_name=project_name
    )

    logger.info('Ready to rumble!')

    return True


if __name__ == '__main__':  # pragma: no cover
    run_main()
