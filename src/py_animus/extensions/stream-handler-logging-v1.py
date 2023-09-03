"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

from py_animus.models import ManifestBase, all_scoped_values, variable_cache, Action, actions
import logging
import traceback
import copy


class StreamHandlerLogging(ManifestBase):

    def __init__(self, post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)
        self.register_action(action_name='Configure StreamHandler Logging', initial_status=Action.UNKNOWN)

    def implemented_manifest_differ_from_this_manifest(self, target_environment: str='default')->bool:
        actions = variable_cache.get_value(variable_name='ALL_ACTIONS')
        if 'Configure StreamHandler Logging' in actions:
            if actions['Configure StreamHandler Logging'] == 'No Action':
                return True
        return False
    
    def determine_actions(self, target_environment: str='default')->list:
        if self.implemented_manifest_differ_from_this_manifest is True:
            self.register_action(action_name='Configure StreamHandler Logging', initial_status=Action.APPLY_PENDING)
        return actions.get_action_values_for_manifest(kind=self.kind, name=self.metadata['name'])

    def apply_manifest(self, target_environment: str='default'): 
        actions = self.determine_actions(target_environment=target_environment)
        if 'Logging Configuration for StreamHandler Log Handler Pending' in actions:
            # TODO configure stream handler logging
            pass
        return
    
    def delete_manifest(self, target_environment: str='default'):
        return self.apply_manifest(target_environment=target_environment)

