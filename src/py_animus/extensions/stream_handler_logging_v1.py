"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

from py_animus.models import all_scoped_values, variable_cache, Action, actions
from py_animus.animus_logging import logger
from py_animus.models.extensions import ManifestBase
import logging
import traceback
import copy
import sys


class StreamHandlerLogging(ManifestBase):
    """
        Spec fields:

        | Field                       | Type    | Required | Default Value                               | Description        |
        |-----------------------------|---------|----------|---------------------------------------------|--------------------|
        | level                       | str     | No       | `info`                                      | The logging level  |
        | loggingFormat               | str     | No       | `'%(asctime)s %(levelname)s - %(message)s'` | The message format |
    """

    def __init__(self, post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def implemented_manifest_differ_from_this_manifest(self, target_environment: str='default')->bool:
        actions = variable_cache.get_value(variable_name='ALL_ACTIONS')
        if 'Configure StreamHandler Logging' in actions:
            if actions['Configure StreamHandler Logging'] == Action.NO_ACTION:
                return True
        return False
    
    def determine_actions(self)->list:
        self.register_action(action_name='Configure StreamHandler Logging', initial_status=Action.UNKNOWN)
        if self.implemented_manifest_differ_from_this_manifest is True:
            self.register_action(action_name='Configure StreamHandler Logging', initial_status=Action.APPLY_PENDING)
        return actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name'])

    def _configure_logging(self):
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
            log_format = self.spec('loggingFormat')
        h = logging.StreamHandler(sys.stdout)
        h.setLevel(log_level)    
        h.setFormatter(log_format)
        logger.addHandler(h)

    def apply_manifest(self): 
        for action_name, expected_action in actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name']).items():
            if action_name == 'Configure StreamHandler Logging' and expected_action == Action.APPLY_PENDING:
                self._configure_logging()
                actions.add_or_update_action(action=Action(manifest_kind=self.kind, manifest_name=self.metadata['name'], action_name=Action.APPLY_DONE))
        logger.info('StreamHandlerLogging configuration done')
        return
    
    def delete_manifest(self):
        return self.apply_manifest()

