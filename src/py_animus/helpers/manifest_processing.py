"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import copy
import sys
import importlib
import os
import inspect

from py_animus.animus_logging import logger
from py_animus.models import all_scoped_values, variable_cache, scope, ScopedValues, Value, actions, Variable
from py_animus.helpers.file_io import file_exists
from py_animus.helpers.yaml_helper import spit_yaml_text_from_file_with_multiple_yaml_sections, load_from_str_and_ignore_custom_tags, parse_animus_formatted_yaml
from py_animus.utils.http_requests_io import download_files
from py_animus.extensions import UnitOfWork, execution_plan, extensions


class ProjectExecutionTracker:

    def __init__(self):
        self.executed_projects = list()

    def mark_project_as_executed(self, project_name: str):
        if project_name not in self.executed_projects:
            self.executed_projects.append(project_name)

    def can_execute_project(self, project_name: str):
        if project_name in self.executed_projects:
            return False
        return True
    
    def reset(self):
        self.executed_projects = list()


tracker = ProjectExecutionTracker()


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


def _process_values_sections(manifest_yaml_sections: dict)->dict:
    if 'Values' in manifest_yaml_sections:
        for value_manifest_section_text in manifest_yaml_sections['Values']:
            _parse_values_data(manifest_data=load_from_str_and_ignore_custom_tags(value_manifest_section_text)['part_1'])
        manifest_yaml_sections.pop('Values')
    return manifest_yaml_sections


def _process_logging_sections(manifest_yaml_sections: dict)->dict:
    logging_configured = variable_cache.get_value(
        variable_name='std:logging_configured',
        value_if_expired=False,
        default_value_if_not_found=False,
        raise_exception_on_expired=False,
        raise_exception_on_not_found=False
    )
    if logging_configured is False:
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
    variable_cache.store_variable(
        variable=Variable(
            name='std:logging_configured',
            initial_value=True
        ),
        overwrite_existing=True
    )
    logger.info('Logging ready')
    return manifest_yaml_sections


def convert_yaml_to_extension_instances(yaml_sections: dict=None):
    for manifest_kind, manifest_yaml_string in yaml_sections.items():
        logger.debug('Converting raw yaml with kind "{}"'.format(manifest_kind))
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


def extract_yaml_section_from_supplied_manifest_file(manifest_uri: str)->dict:
    final_manifest_file_to_parse = '{}'.format(manifest_uri)
    if manifest_uri.lower().startswith('http'):
        files = download_files(urls=[manifest_uri,])
        if len(files) > 0:
            final_manifest_file_to_parse = files[0]

    if file_exists(final_manifest_file_to_parse) is False:
        raise Exception('Manifest file "{}" does not exist!'.format(final_manifest_file_to_parse))
    
    return spit_yaml_text_from_file_with_multiple_yaml_sections(yaml_text=final_manifest_file_to_parse)


def get_modules_in_package(files: list):
    for file in files:
        path_portion = '{}'.format(os.sep).join(file.split(os.sep)[0:-1])
        if path_portion not in sys.path:
            sys.path.insert(0,path_portion)
            logger.info('Added path "{}" to sys.path'.format(path_portion))
        if file not in ['__init__.py', '__pycache__']:
            if file[-3:] != '.py':
                logger.warning('File "{}" not a Python file - ignoring'.format(file))
                continue    # pragma: no cover
            file_name = file[:-3]
            module_name = file_name
            # module_name = module_name.replace('{}'.format(os.sep), '', 1).replace('{}'.format(os.sep), '.')
            module_name = module_name.split('{}'.format(os.sep))[-1]
            logger.info('Attempting to add module named "{}" from file "{}"'.format(module_name, file_name))
            for name, cls in inspect.getmembers(importlib.import_module(module_name), inspect.isclass):
                if cls.__module__ == module_name:
                    m = importlib.import_module(module_name)
                    clazz = getattr(m, name)
                    yield (clazz, name)


def process_project(project_manifest_uri: str, project_name: str):
    if project_name is None:
        raise Exception('The named project manifest was not found in the supplied manifest file. Cannot continue.')
    yaml_sections = extract_yaml_section_from_supplied_manifest_file(manifest_uri=project_manifest_uri)
    yaml_sections = _process_values_sections(manifest_yaml_sections=yaml_sections)
    if len(yaml_sections) == 0:
        raise Exception('No manifests present')
    if 'Project' not in yaml_sections:
        raise Exception('No projects found in the supplied Manifest file')
    for yaml_section in yaml_sections['Project']:
        project_instance = parse_animus_formatted_yaml(raw_yaml_str=yaml_section)

        if tracker.can_execute_project(project_name=project_instance.metadata['name']) is False:
            return
        tracker.mark_project_as_executed(project_name=project_instance.metadata['name'])

        project_instance_variables_base_name = '{}:{}:{}:'.format(
            project_instance.__class__.__name__,
            project_instance.metadata['name'],
            scope.value
        )
        in_scope = True
        if 'environments' in project_instance.metadata:
            if scope.value not in project_instance.metadata['environments']:
                in_scope = False
                logger.info('Project "{}" not in scope (scope not found in environments)'.format(project_instance.metadata['name']))
        elif scope.value != 'default':
            logger.info('Project "{}" not in scope (non-default scope with no environments defined in project manifest)'.format(project_instance.metadata['name']))
            in_scope = False
        if project_instance.metadata['name'] != project_name:
            logger.info('Project "{}" not selected as name does not match the selected project name "{}"'.format(project_instance.metadata['name'], project_name))
            in_scope = False
        if in_scope:
            if 'parentProjects' in project_instance.spec:
                if isinstance(project_instance.spec['parentProjects'], list):
                    for parent_project_data in project_instance.spec['parentProjects']:
                        if 'name' in parent_project_data and 'path' in parent_project_data:
                            process_project(project_manifest_uri=parent_project_data['path'], project_name=parent_project_data['name'])
            logger.info('Project "{}" selected for processing'.format(project_instance.metadata['name']))
            project_instance.determine_actions()

            # Process values
            logger.debug('Values processing for project "{}" starting'.format(project_instance.metadata['name']))
            if 'valuesConfig' in project_instance.spec:
                for values_config_uri in project_instance.spec['valuesConfig']:
                    potential_values_yaml_sections = extract_yaml_section_from_supplied_manifest_file(manifest_uri=values_config_uri)
                    _process_values_sections(manifest_yaml_sections=potential_values_yaml_sections)
            logger.debug('   Values processing for project "{}" completed'.format(project_instance.metadata['name']))

            # Process logging
            logger.debug('Logging processing for project "{}" starting'.format(project_instance.metadata['name']))
            logging_manifest = variable_cache.get_value(
                variable_name='LOGGING_CONFIG',
                value_if_expired=None,
                default_value_if_not_found=None,
                raise_exception_on_expired=False,
                raise_exception_on_not_found=False
            )
            if logging_manifest is not None:
                potential_logging_yaml_sections = extract_yaml_section_from_supplied_manifest_file(manifest_uri=logging_manifest)
                _process_logging_sections(manifest_yaml_sections=potential_logging_yaml_sections)
                project_instance.reset_logger()
            logger.debug('   Logging processing for project "{}" completed'.format(project_instance.metadata['name']))

            # Load Extensions
            logger.debug('Extensions processing for project "{}" starting'.format(project_instance.metadata['name']))
            project_instance.collect_extension_files()
            extension_files = variable_cache.get_value(
                variable_name='{}PROJECT_EXTENSION_FILES'.format(project_instance_variables_base_name),
                value_if_expired=list(),
                default_value_if_not_found=list(),
                raise_exception_on_expired=False,
                raise_exception_on_not_found=False
            )
            for returned_class, kind in get_modules_in_package(files=extension_files):
                extensions.add_extension(extension=returned_class)
                logger.info('Added extension kind "{}"'.format(kind))
            
            logger.debug('   Extensions processing for project "{}" completed'.format(project_instance.metadata['name']))
            logger.debug('Extensions Ingested: {}'.format(str(extensions)))

            # Load manifest files and parse sections.
            logger.debug('Manifest processing for project "{}" starting'.format(project_instance.metadata['name']))
            combined_project_manifest_sections = dict()
            final_combined_project_manifest_sections = dict()
            for project_manifest_file_or_url in project_instance.spec['manifestFiles']:
                combined_project_manifest_sections = {**combined_project_manifest_sections, **extract_yaml_section_from_supplied_manifest_file(manifest_uri=project_manifest_file_or_url)}
            for section_name, section_data in combined_project_manifest_sections.items():
                if section_name != 'Project' and section_name != 'Values' and section_name.endswith('Logging') is False:
                    final_combined_project_manifest_sections[section_name] = copy.deepcopy(section_data)

            # Add sections to execution plan
            convert_yaml_to_extension_instances(yaml_sections=final_combined_project_manifest_sections)
            execution_plan.calculate_execution_plan()
            logger.info('Project "{}" Execution Plan: {}'.format(project_name, execution_plan.execution_order))

            # The idea now is that the project extension sets various variables for next actions
            execution_plan.do_work(scope=scope.value, action=actions.command)
            if actions.command == 'apply':
                project_instance.metadata = project_instance.resolve_all_pending_variables(iterable=copy.deepcopy(project_instance.metadata))
                project_instance.spec = project_instance.resolve_all_pending_variables(iterable=copy.deepcopy(project_instance.spec))
                project_instance.apply_manifest()
            elif actions.command == 'delete':
                project_instance.metadata = project_instance.resolve_all_pending_variables(iterable=copy.deepcopy(project_instance.metadata))
                project_instance.spec = project_instance.resolve_all_pending_variables(iterable=copy.deepcopy(project_instance.spec))
                project_instance.delete_manifest()
            else:
                raise Exception('Unrecognized Command "{}" - expected either "apply" or "delete"'.format(actions.command))
            logger.debug('   Manifest processing for project "{}" completed'.format(project_instance.metadata['name']))
            
            project_instance_variable_names = variable_cache.get_all_variable_names_staring_with(project_instance_variables_base_name)
            logger.debug('Collected variable names: {}'.format(project_instance_variable_names))
        else:
            logger.info('Project "{}" not in scope for processing'.format(project_instance.metadata['name']))
    return

