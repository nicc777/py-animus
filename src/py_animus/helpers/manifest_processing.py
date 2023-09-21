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
from py_animus.utils.http_requests_io import download_files
from py_animus.animus_logging import logger
from py_animus.extensions import UnitOfWork, execution_plan


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


def _process_values_sections(manifest_yaml_sections: dict, process_values: bool=False)->dict:
    if 'Values' in manifest_yaml_sections:
        if process_values is True:
            for value_manifest_section_text in manifest_yaml_sections['Values']:
                _parse_values_data(manifest_data=load_from_str_and_ignore_custom_tags(value_manifest_section_text)['part_1'])
            manifest_yaml_sections.pop('Values')
    return manifest_yaml_sections


def _process_logging_sections(manifest_yaml_sections: dict, process_logging: bool=False)->dict:
    if process_logging is True:
        logging_actions = list()
        for logging_kind in ('StreamHandlerLogging', 'FileHandlerLogging',):
            if logging_kind in manifest_yaml_sections:
                for value_manifest_section_text in manifest_yaml_sections[logging_kind]:
                    stream_logging_instance = parse_animus_formatted_yaml(raw_yaml_str=value_manifest_section_text)
                    stream_logging_instance.determine_actions()
                    logging_actions.append(stream_logging_instance)
                manifest_yaml_sections.pop(logging_kind)
        for logging_extension in logging_actions:
            logging_extension.apply_manifest()
    logger.info('Logging ready')
    return manifest_yaml_sections


def read_manifest_and_extract_individual_yaml_sections(start_manifest: str, process_values: bool=False, process_logging: bool=False)->dict:
    extracted_yaml_sections = spit_yaml_text_from_file_with_multiple_yaml_sections(yaml_text=start_manifest)
    remaining_extracted_yaml_sections = _process_values_sections(manifest_yaml_sections=copy.deepcopy(extracted_yaml_sections), process_values=process_values)
    final_yaml_sections = _process_logging_sections(manifest_yaml_sections=copy.deepcopy(remaining_extracted_yaml_sections), process_logging=process_logging)
    return final_yaml_sections


def convert_yaml_to_extension_instances():
    yaml_sections = variable_cache.get_value(
        variable_name='std::all-yaml-sections',
        value_if_expired=dict(),
        default_value_if_not_found=dict(),
        raise_exception_on_expired=False,
        raise_exception_on_not_found=False
    )
    for manifest_kind, manifest_yaml_string in yaml_sections.items():
        logger.info('Converting raw yaml with kind "{}"'.format(manifest_kind))
        if manifest_kind != 'Project' and manifest_kind != 'Values' and manifest_kind.endswith('Logging') is False:
            for yaml_section in manifest_yaml_string:
                work_instance = parse_animus_formatted_yaml(raw_yaml_str=yaml_section)
                in_scope = True
                if 'environments' in work_instance.metadata:
                    if scope.value not in work_instance.metadata['environments']:
                        in_scope = False
                        logger.info('Manifest "{}" not in scope (scope not found in environments)'.format(work_instance.metadata['name']))
                elif scope.value != 'default':
                    logger.info('Manifest "{}" not in scope (non-default scope with no environments defined in project manifest)'.format(work_instance.metadata['name']))
                    in_scope = False
                if in_scope:
                    execution_plan.all_work.add_unit_of_work(
                        unit_of_work=UnitOfWork(
                            work_instance=work_instance
                        )
                    )


def process_selected_project():
    project_name = variable_cache.get_value(
        variable_name='std::project-name',
        value_if_expired=None,
        default_value_if_not_found=None,
        raise_exception_on_expired=False,
        raise_exception_on_not_found=False
    )
    yaml_sections = variable_cache.get_value(
        variable_name='std::all-yaml-sections',
        value_if_expired=dict(),
        default_value_if_not_found=dict(),
        raise_exception_on_expired=False,
        raise_exception_on_not_found=False
    )
    if project_name is None:
        raise Exception('The named project manifest was not found in the supplied manifest file. Cannot continue.')
    if 'Project' not in yaml_sections:
        raise Exception('No projects found in the supplied Manifest file')
    for yaml_section in yaml_sections['Project']:
        work_instance = parse_animus_formatted_yaml(raw_yaml_str=yaml_section)
        in_scope = True
        if 'environments' in work_instance.metadata:
            if scope.value not in work_instance.metadata['environments']:
                in_scope = False
                logger.info('Project "{}" not in scope (scope not found in environments)'.format(work_instance.metadata['name']))
        elif scope.value != 'default':
            logger.info('Project "{}" not in scope (non-default scope with no environments defined in project manifest)'.format(work_instance.metadata['name']))
            in_scope = False
        if work_instance.metadata['name'] != project_name:
            logger.info('Project "{}" not selected as manifest name "{}" does not match the selected project name "{}"'.format(work_instance.metadata['name'], project_name))
            in_scope = False
        if in_scope:
            variable_cache.store_variable(
                variable=Variable(
                    name='function::convert_yaml_to_extension_instances',
                    initial_value=convert_yaml_to_extension_instances
                ),
                overwrite_existing=False
            )
            logger.info('Project "{}" selected for processing'.format(work_instance.metadata['name']))
            execution_plan.all_work.add_unit_of_work(
                unit_of_work=UnitOfWork(
                    work_instance=work_instance
                )
            )
            # TODO execute project action


def parse_project_manifest_items(yaml_sections: dict, project_name: str):
    ###
    ### Process manifests defined within the scope
    ###
    # TODO - now parse Project and execute... If project has other project dependencies, parse those now first...
    for manifest_kind, manifest_yaml_string in yaml_sections.items():
        logger.info('Processing raw yaml with kind "{}"'.format(manifest_kind))
        if manifest_kind == 'Project': 
            for yaml_section in manifest_yaml_string:
                work_instance = parse_animus_formatted_yaml(raw_yaml_str=yaml_section)
                in_scope = True
                if 'environments' in work_instance.metadata:
                    if scope.value not in work_instance.metadata['environments']:
                        in_scope = False
                        logger.info('Project "{}" not in scope (scope not found in environments)'.format(work_instance.metadata['name']))
                elif scope.value != 'default':
                    logger.info('Project "{}" not in scope (non-default scope with no environments defined in project manifest)'.format(work_instance.metadata['name']))
                    in_scope = False
                if in_scope:
                    if work_instance.metadata['name'] == project_name:
                        logger.info('Project "{}" selected for processing'.format(work_instance.metadata['name']))
                        execution_plan.all_work.add_unit_of_work(
                            unit_of_work=UnitOfWork(
                                work_instance=work_instance
                            )
                        )
                    else:
                        logger.info('Project "{}" not selected for processing (project name mismatch)'.format(work_instance.metadata['name']))
                else:
                    logger.info('Project "{}" not selected for processing (scope/environment mismatch)'.format(work_instance.metadata['name']))
        else:
            if manifest_kind != 'Project': # We process this last...
                for yaml_section in manifest_yaml_string:
                    work_instance = parse_animus_formatted_yaml(raw_yaml_str=yaml_section)
                    in_scope = True
                    if 'environments' in work_instance.metadata:
                        if scope.value not in work_instance.metadata['environments']:
                            in_scope = False
                            logger.info('Manifest "{}" not in scope (scope not found in environments)'.format(work_instance.metadata['name']))
                    elif scope.value != 'default':
                        logger.info('Manifest "{}" not in scope (non-default scope with no environments defined in project manifest)'.format(work_instance.metadata['name']))
                        in_scope = False
                    if in_scope:
                        execution_plan.all_work.add_unit_of_work(
                            unit_of_work=UnitOfWork(
                                work_instance=work_instance
                            )
                        )
    execution_plan.calculate_execution_plan()
    calculated_execution_plan = execution_plan.execution_order
    logger.info('Current calculated execution plan: {}'.format(calculated_execution_plan))
    execution_plan.do_work(scope=scope.value, action=actions.command)

