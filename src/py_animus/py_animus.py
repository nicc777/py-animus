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
    logger.info('Returning CLI Argument Parser')
    return parser


def apply_command(vc, mm, logger):
    for name in tuple(mm.manifest_instances.keys()):
        logger.debug('Applying manifest named "{}"'.format(name))
        mm.apply_manifest(name=name)
    for name in tuple(vc.values.keys()):
        logger.info('RESULT: {}={}'.format(name, vc.get_value(variable_name=name)))


def delete_command(vc, mm, logger):
    for name in tuple(mm.manifest_instances.keys()):
        logger.debug('Deleting manifest named "{}"'.format(name))
        mm.delete_manifest(name=name)
    for name in tuple(vc.values.keys()):
        logger.info('RESULT: {}={}'.format(name, vc.get_value(variable_name=name)))


def main(logger=get_logger(), command: str=sys.argv[1], cli_args: list=sys.argv[2:]):
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
    
    logger.debug('Command line arguments parsed...')
    logger.debug('   parsed_args: {}'.format(parsed_args))
    logger.debug('   unknown_args: {}'.format(unknown_args))
    manifest_files = parsed_args.manifest_locations
    vc = VariableCache()
    mm = ManifestManager(variable_cache=vc)
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
        apply_command(vc, mm, logger)
    elif command == 'delete':
        delete_command(vc, mm, logger)
    else:
        raise Exception('Unknown command. Command must be one of "apply" or "delete"')


if __name__ == '__main__':
    main()

