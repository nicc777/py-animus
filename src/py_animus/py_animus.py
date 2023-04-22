"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""
import sys
from py_animus import get_logger, parse_raw_yaml_data
from py_animus.manifest_management import *
import argparse


def _get_arg_parser(
    logger
)->argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog = 'animus COMMAND',
        description='Processes YAML manifest files and call custom user defined implementation logic to act on te manifest files',
        epilog = 'COMMAND is one of "apply" or "delete"'
    )
    parser.add_argument(
        '-m', '--manifest',
        action='append',
        nargs='*',
        dest='manifest_locations',
        metavar='LOCATION',
        type=str, 
        required=True,
        help='[REQUIRED] Points to one or more YAML manifest files that will be read in and parsed.'
    )
    parser.add_argument(
        '-s', '--src',
        action='append',
        nargs='*',
        dest='src_locations',
        metavar='LOCATION',
        type=str, 
        required=True,
        help='[REQUIRED] One or more Python files that implement the logic to handle the manifest files.'
    )
    parser.add_argument(
        '-e', '--env',
        action='append',
        nargs='*',
        dest='environments',
        metavar='ENVIRONMENT',
        type=str, 
        required=False,
        help='[OPTIONAL] One or more environments to target. Environment will be synchronized one at a time.'
    )
    parser.add_argument(
        '-f', '--file',
        action='append',
        nargs='*',
        dest='values_files',
        metavar='VALUES_FILE',
        type=str, 
        required=False,
        default=['/tmp/values/values.yaml', ],
        help='[OPTIONAL] One or more values files to use for environment variable substitution.'
    )
    logger.info('Returning CLI Argument Parser')
    return parser


def apply_command(vc: VariableCache, mm: ManifestManager, logger, target_environments: list=['default',]):
    for target_environment in target_environments:
        logger.info('TARGET ENVIRONMENT: {}'.format(target_environment))
        for name in tuple(mm.manifest_instances.keys()):
            logger.info('Applying manifest named "{}"'.format(name))
            mm.apply_manifest(name=name, target_environment=target_environment)
        for name in tuple(vc.values.keys()):
            logger.info('RESULT: {}={}'.format(name, vc.get_value(variable_name=name, for_logging=True)))


def delete_command(vc: VariableCache, mm: ManifestManager, logger, target_environments: list=['default',]):
    for target_environment in target_environments:
        logger.info('TARGET ENVIRONMENT: {}'.format(target_environment))
        for name in tuple(mm.manifest_instances.keys()):
            logger.info('Deleting manifest named "{}"'.format(name))
            mm.delete_manifest(name=name, target_environment=target_environment)
        for name in tuple(vc.values.keys()):
            logger.info('RESULT: {}={}'.format(name, vc.get_value(variable_name=name, for_logging=True)))


def main(command: str, cli_args: list, logger=get_logger()):
    logger.info('ok')
    if command.lower().startswith('--h') or command.lower().startswith('-h'):
        cli_args=['-h', ]
    args = dict()
    args['conf'] = None
    parser = _get_arg_parser(logger=logger)
    parsed_args, unknown_args = parser.parse_known_args(cli_args)
    
    if not command:
        raise Exception('Expected command "apply" or "delete"')
    if command not in ('apply', 'delete'):
        raise Exception('Command must be one of "apply" or "delete"')
    
    target_environments = ['default',]
    logger.debug('parsed_args.environments: {}'.format(parsed_args.environments))
    if parsed_args.environments:
        target_environments = list()
        if isinstance(parsed_args.environments, list):
            for item in parsed_args.environments:
                if isinstance(item, list):
                    for e_item in item:
                        target_environments.append(e_item)
                elif isinstance(item, str):
                    target_environments = target_environments.append(item)
        elif isinstance(parsed_args.environments, str):
            target_environments.append(parsed_args.environments)
    values_files = parsed_args.values_files
    if isinstance(values_files, str) is True:
        values_files = [ values_files, ]
    if isinstance(target_environments, str) is True:
        target_environments = [ target_environments, ]
    
    logger.debug('Command line arguments parsed...')
    logger.debug('   parsed_args         : {}'.format(parsed_args))
    logger.debug('   unknown_args        : {}'.format(unknown_args))
    logger.debug('   target_environments : {}'.format(target_environments))
    logger.debug('   values_files        : {}'.format(values_files))
    vc = VariableCache()
    mm = ManifestManager(variable_cache=vc, environments=target_environments, values_files=values_files)
    for src_file_list in parsed_args.src_locations:
        for src_file in src_file_list:
            logger.debug('Ingesting source file {}'.format(src_file))
            mm.load_manifest_class_definition_from_file(plugin_file_path=src_file)
    for manifest_file_list in parsed_args.manifest_locations:
        for manifest_file in manifest_file_list:
            try:
                data = ''
                with open(manifest_file, 'r') as f:
                    data = f.read()
                parsed_data = parse_raw_yaml_data(yaml_data=data, logger=logger)
                for part_id, data_as_dict in parsed_data.items():
                    if 'version' in data_as_dict and 'kind' in data_as_dict and 'metadata' in data_as_dict:
                        mm.parse_manifest(manifest_data=data_as_dict)
            except:
                logger.error('Failed to read file "{}" due to exception'.format(manifest_file))
                logger.error(traceback.format_exc())
    
    if command == 'apply':
        apply_command(vc, mm, logger, target_environments=target_environments)
    elif command == 'delete':
        delete_command(vc, mm, logger, target_environments=target_environments)
    else:
        raise Exception('Unknown command. Command must be one of "apply" or "delete"')
    return (vc, mm)


def run_main(logger=get_logger()):
    command = '-h'
    cli_args = list()
    logger.info('sys.argv={}'.format(sys.argv))
    if len(sys.argv) > 1:
        if sys.argv[1] in ('apply', 'delete',) or sys.argv[1].startswith('-h') is True or sys.argv[1].startswith('--h') is True:
            command = sys.argv[1]
        if len(sys.argv) > 2:
            cli_args = sys.argv[2:]
        else:
            command = '-h'
    return main(command=command, cli_args=cli_args, logger=get_logger())

if __name__ == '__main__':
    run_main()

