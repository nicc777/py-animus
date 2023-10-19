"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

from py_animus.models import all_scoped_values, variable_cache, Action, actions
from py_animus.animus_logging import logger, add_handler
from py_animus.models.extensions import ManifestBase
import logging
import logging.handlers
import sys


class RotatingFileHandlerLogging(ManifestBase): # pragma: no cover
    """# `RotatingFileHandlerLogging` Description
     
Logs to a file on the local system. The log file will be appended until 
`maxBytes` is reached (default=10 MiB). The number of backups kept is 
determined by the `backupCount` setting (default=5).

# Apply Action

Configures the logger

# Delete Action

Automatically redirects to the `apply` action

# Variables 

## After Apply Action

No variables are set

## After Delete Action

No variables are set or deleted

## Spec fields

| Field                       | Type    | Required | Default Value                               | Description                                                  |
|-----------------------------|---------|----------|---------------------------------------------|--------------------------------------------------------------|
| level                       | str     | No       | `info`                                      | The logging level                                            |
| loggingFormat               | str     | No       | `'%(asctime)s %(levelname)s - %(message)s'` | The message format                                           |
| filename                    | str     | yes      | None (will cause Exception to be raised)    | The log file name                                            |
| maxBytes                    | int     | No       | 10 MiB                                      | How many bytes to log before rotating the log file           |
| backupCount                 | int     | No       | 5                                           | HOw many files to keep before starting to delete old files.  | 
    """

    def __init__(self, post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def implemented_manifest_differ_from_this_manifest(self)->bool:
        if 'filename' not in self.spec:
            raise Exception('Property "filename" ikn spec is required.')
        if actions.get_action_status(manifest_kind=self.kind, manifest_name=self.metadata['name'], action_name='Configure FileHandler Logging') == Action.APPLY_DONE:
            return False
        return True
    
    def determine_actions(self)->list:
        self.register_action(action_name='Configure FileHandler Logging', initial_status=Action.UNKNOWN)
        if self.implemented_manifest_differ_from_this_manifest() is True:
            self.register_action(action_name='Configure FileHandler Logging', initial_status=Action.APPLY_PENDING)
        return actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name'])

    def _configure_logging(self):

        max_bytes = 10 * 1024 * 1024
        backup_count = 5

        if 'maxBytes' in self.spec:
            max_bytes = int(self.spec['maxBytes'])

        if 'backupCount' in self.spec:
            backup_count = int(self.spec['backupCount'])

        log_format = '%(asctime)s %(levelname)s - %(message)s'
        log_level = logging.INFO
        if 'level' in self.spec:
            if self.spec['level'].lower().startswith('d') is True:
                log_level = logging.DEBUG
            if self.spec['level'].lower().startswith('e') is True:
                log_level = logging.ERROR
            if self.spec['level'].lower().startswith('c') is True:
                log_level = logging.CRITICAL
        if 'loggingFormat' in self.spec:
            log_format = self.spec['loggingFormat']
        formatter = logging.Formatter(log_format)
        h = logging.handlers.RotatingFileHandler(filename=self.spec['filename'], maxBytes=max_bytes, backupCount=backup_count)
        h.setLevel(log_level)
        h.setFormatter(formatter)
        add_handler(h)

    def apply_manifest(self): 
        for action_name, expected_action in actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name']).items():
            if action_name == 'Configure FileHandler Logging' and expected_action == Action.APPLY_PENDING:
                self._configure_logging()
                actions.add_or_update_action(action=Action(manifest_kind=self.kind, manifest_name=self.metadata['name'], action_name='Configure FileHandler Logging', action_status=Action.APPLY_DONE))
        logger.info('FileHandlerLogging configuration done')
        return
    
    def delete_manifest(self):
        self.log(message='Logging "delete" actions automatically redirects to an apply action.', level='warning')
        return self.apply_manifest()

