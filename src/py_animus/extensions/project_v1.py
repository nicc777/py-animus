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
import sys


class Project(ManifestBase):   # pragma: no cover
    """
        Spec fields:

        | Field                       | Type    | Required | Default Value                               | Description                                                                               |
        |-----------------------------|---------|----------|---------------------------------------------|-------------------------------------------------------------------------------------------|
        | actions.apply               | list    | yes      | No Default                                  | The list of at least one named manifest that must be applied for this project.            |
        | actions.delete              | list    | yes      | No Default                                  | The list of at least one named manifest that must be deleted when the project is deleted. |
    """

    def __init__(self, post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def implemented_manifest_differ_from_this_manifest(self)->bool:
        if actions.get_action_status(manifest_kind=self.kind, manifest_name=self.metadata['name'], action_name='Project Action') == Action.APPLY_DONE:
            return False
        return True
    
    def determine_actions(self)->list:
        self.register_action(action_name='Project Action', initial_status=Action.UNKNOWN)
        if self.implemented_manifest_differ_from_this_manifest() is True:
            self.register_action(action_name='Project Action', initial_status=Action.APPLY_PENDING)
        return actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name'])

    def apply_manifest(self): 
        for action_name, expected_action in actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name']).items():
            if action_name == 'Project Action' and expected_action == Action.APPLY_PENDING:
                actions.add_or_update_action(action=Action(manifest_kind=self.kind, manifest_name=self.metadata['name'], action_name='Project Action', action_status=Action.APPLY_DONE))
        logger.info('Project Applied')
        return
    
    def delete_manifest(self):
        logger.info('Project Deleted')
        return

