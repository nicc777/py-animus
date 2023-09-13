"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import copy
import json
from py_animus.extensions.stream_handler_logging_v1 import StreamHandlerLogging as StreamHandlerLoggingV1
from py_animus.extensions.file_handler_logging_v1 import FileHandlerLogging as FileHandlerLoggingV1
from py_animus.extensions.syslog_handler_logging_v1 import SyslogHandlerLogging as SyslogHandlerLoggingV1
from py_animus.extensions.datagram_handler_logging_v1 import DatagramHandlerLogging as DatagramHandlerLoggingV1
from py_animus.extensions.shell_script_v1 import ShellScript as ShellScriptV1
from py_animus.extensions.project_v1 import Project as ProjectV1
from py_animus.animus_logging import logger
from py_animus.models.extensions import ManifestBase


class AnimusExtensions:

    def __init__(self):
        self.extensions = dict()
        self.supported_versions_of_extensions = dict()

    def add_extension(self, extension: ManifestBase):
        if extension is None:
            return
        try:
            extension.__name__     # If this works, extension was not Initialized
        except:
            pass
        initialized_extension = extension()
        if isinstance(initialized_extension, ManifestBase) is False:
            raise Exception('Unsupported Extension')
        initialized_extension_kind = copy.deepcopy(initialized_extension.kind)
        version = copy.deepcopy(initialized_extension.version)
        idx = '{}:{}'.format(initialized_extension_kind, version)
        if idx not in self.extensions:
            self.extensions[idx] = extension
        if idx not in self.supported_versions_of_extensions:
            self.supported_versions_of_extensions[idx] = copy.deepcopy(initialized_extension.supported_versions)

    def find_extension_that_supports_version(self, extension_kind: str, version: str)->ManifestBase:
        idx = '{}:{}'.format(extension_kind, version)
        if idx in self.extensions:
            return copy.deepcopy(self.extensions[idx])
        for idx, supported_versions in self.supported_versions_of_extensions.items():
            available_extension_kind = idx.split(':')[0]
            if available_extension_kind == extension_kind:
                if version in supported_versions:
                    return copy.deepcopy(self.extensions[idx])
        raise Exception('Extension kind "{}" of version "{}" was not found'.format(extension_kind, version))
                

extensions = AnimusExtensions()

# Add standard extensions
extensions.add_extension(extension=StreamHandlerLoggingV1)
extensions.add_extension(extension=FileHandlerLoggingV1)
extensions.add_extension(extension=SyslogHandlerLoggingV1)
extensions.add_extension(extension=DatagramHandlerLoggingV1)
extensions.add_extension(extension=ShellScriptV1)
extensions.add_extension(extension=ProjectV1)



class UnitOfWork:

    def __init__(self, work_instance: ManifestBase):
        self.id = '{}'.format(
            work_instance.metadata['name'],
        )
        self.scopes = ['default',]
        self.dependencies = dict()
        self.work_instance = work_instance

        if 'dependencies' in work_instance.metadata:
            for a_action, action_dependencies in work_instance.metadata['dependencies']:
                self.dependencies[a_action] = action_dependencies

        if 'environments' in self.work_instance.metadata:
            self.scopes = copy.deepcopy(work_instance.metadata['environments'])

        logger.info('UnitOfWork: Manifest named "{}" registered as a UnitOfWork'.format(self.id))

    def run(self, action: str, scope: str):
        if scope in self.scopes is True:
            logger.warning(
                'UnitOfWork: "{}:{}" marked for executed for scope named "{}"'.format(
                    self.work_instance.kind,
                    self.work_instance.metadata['name'],
                    scope
                )
            )
            if action == 'apply':
                if 'skipApplyAll' in self.work_instance.metadata:
                    if self.work_instance.metadata['skipApplyAll'] is True:
                        logger.warning(
                            'UnitOfWork "{}:{}" will not be executed because  "skipApplyAll" was set to True'.format(
                                self.work_instance.kind,
                                self.work_instance.metadata['name']
                            )
                        )
                        return
                self.work_instance.apply_manifest()
            if action == 'delete':
                if 'skipDeleteAll' in self.work_instance.metadata:
                    if self.work_instance.metadata['skipDeleteAll'] is True:
                        logger.warning(
                            'UnitOfWork "{}:{}" will not be executed because  "skipDeleteAll" was set to True'.format(
                                self.work_instance.kind,
                                self.work_instance.metadata['name']
                            )
                        )
                        return
                self.work_instance.delete_manifest()
        else:
            logger.warning(
                'UnitOfWork "{}:{}" is not in scope for scope named "{}"'.format(
                    self.work_instance.kind,
                    self.work_instance.metadata['name'],
                    scope
                )
            )
        return


class AllWork:

    def __init__(self):
        self.all_work_list = list()

    def unit_of_work_by_id_exists(self, id: str)->bool:
        for uow in self.all_work_list:
            if uow.id == id:
                return True
        return False

    def add_unit_of_work(self, unit_of_work: UnitOfWork):
        if self.unit_of_work_by_id_exists(id=unit_of_work.id) is False:
            self.all_work_list.append(unit_of_work)


    def get_unit_of_work_by_id(self, id: str)->UnitOfWork:
        for uow in self.all_work_list:
            if uow.id == id:
                return uow


class ExecutionPlan:

    def __init__(self, all_work:AllWork):
        self.all_work = all_work
        self.execution_order = dict()
        self.execution_order['apply'] = list()
        self.execution_order['delete'] = list()

    def _unit_of_work_contains_skip_action_exclusion(self, uow: UnitOfWork, action: str):
        add_for_action = True
        skip_name = 'skip{}All'.format(action.capitalize())
        if skip_name in uow.work_instance.metadata:
            if uow.work_instance.metadata[skip_name] is True:
                add_for_action = False
        return add_for_action

    def add_unit_of_work_to_execution_order(self, uow: UnitOfWork):
        for a_action, parent_uow_id in uow.dependencies.items():
            add_for_action = self._unit_of_work_contains_skip_action_exclusion(uow=uow, action=a_action)
            if add_for_action is True:
                if a_action not in self.execution_order:
                    self.execution_order[a_action] = list()
                if parent_uow_id not in self.execution_order[a_action]:
                    self.add_unit_of_work_to_execution_order(uow=self.all_work.get_unit_of_work_by_id(id=parent_uow_id))
        for a_action in ('apply', 'delete'):
            add_for_action = self._unit_of_work_contains_skip_action_exclusion(uow=uow, action=a_action)
            if add_for_action is True:
                if a_action not in self.execution_order:
                    self.execution_order[a_action] = list()
                self.execution_order[a_action].append(uow.id)

    def calculate_execution_plan(self):
        for uow in self.all_work.all_work_list:
            self.add_unit_of_work_to_execution_order(uow=uow)

    def do_work(self, scope: str, action: str):
        if len(self.execution_order[action]) == 0:
            self.calculate_execution_plan()
            logger.info('ExecutionPlan: {}'.format(json.dumps(self.execution_order[action], default=str)))
        logger.info('ExecutionPlan: Starting run for action "{}"'.format(action))
        for uof_id in self.execution_order[action]:
            uow = self.all_work.get_unit_of_work_by_id(id=uof_id)
            if scope in uow.scopes:
                logger.info('ExecutionPlan: Calling run action for UnitOfWork named "{}"'.format(uow.id))
                uow.run()
        self.execution_order[action] = list()


execution_plan = ExecutionPlan(all_work=AllWork())
