"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

from py_animus.animus_logging import logger
from py_animus.models import Action, actions, variable_cache, Variable
from py_animus.models.extensions import ManifestBase


class Project(ManifestBase):   # pragma: no cover
    """
        Spec fields:

        | Field                       | Type    | Required | Default Value                               | Description                                                                                                                                                    |
        |-----------------------------|---------|----------|---------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
        | workDirectory               | str     | Yes      | No Default                                  | A directory that will be created to store all temporary artifacts. The directory will be deleted once done.                                                    |
        | parentProjects              | list    | No       | Empty dict                                  | Any additional projects referenced here will be processed first.                                                                                               |
        | parentProjects.[n].name     | str     | Yes (1)  | No Default                                  | The project name                                                                                                                                               |
        | parentProjects.[n].path     | str     | Yes (1)  | No Default                                  | Te path to the file containing the project manifest.                                                                                                           |
        | loggingConfig               | str     | No       | No Default                                  | Path to the manifest containing any "*Logging" type manifests                                                                                                  |
        | valuesConfig                | str     | No       | No Default                                  | Path to the manifest containing any "Values" type manifests                                                                                                    |
        | manifestFiles               | list    | Yes      | Empty list                                  | YAML files/URL's containing manifests to ingest. There must be at least ONE file/URL defined, even if it points to the same file/URL as this project manifest. |
        | extensionPaths              | list    | No       | Empty list                                  | Directories containing third party extensions to ingest                                                                                                        |
        | skipConfirmation            | bool    | No       | False                                       | If `False`, print the execution plan and prompt user to proceed.                                                                                               |

        Notes:

        1. Required in the list of dict objects when `parentProjects` is not an empty list.
    """

    def __init__(self, post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def implemented_manifest_differ_from_this_manifest(self)->bool:
        if 'manifestFiles' not in self.spec:
            raise Exception('Project manifest MUST contain "manifestFiles" with a list of manifest files to ingest and process.')
        if self.spec['manifestFiles'] is None:
            raise Exception('Spec "manifestFiles" can not be NULL')
        if isinstance(self.spec['manifestFiles'], list) is False:
            raise Exception('Spec "manifestFiles" must be a list containing at least ONE file/URL to a manifest file')
        done_action = Action.APPLY_DONE
        if actions.command == 'delete':
            done_action == Action.DELETE_DONE
        if actions.get_action_status(manifest_kind=self.kind, manifest_name=self.metadata['name'], action_name='Project Action') == done_action:
            return False
        return True
    
    def determine_actions(self)->list:
        self.register_action(action_name='Project Action', initial_status=Action.UNKNOWN)
        pending_action = Action.APPLY_PENDING
        if actions.command == 'delete':
            pending_action = Action.DELETE_PENDING
        if self.implemented_manifest_differ_from_this_manifest() is True:
            self.register_action(action_name='Project Action', initial_status=pending_action)

        ###
        ### Process "loggingConfig" in Spec
        ###
        if 'loggingConfig' in self.spec:
            if isinstance(self.spec['loggingConfig'], str):        
                variable_cache.store_variable(
                    variable=Variable(
                        name='LOGGING_CONFIG',
                        initial_value=self.spec['loggingConfig']
                    ),
                    overwrite_existing=True
                )
        
        return actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name'])

    def _process_action(self):
        ###
        ### Process "skipConfirmation" in Spec
        ###
        skip_confirmation = variable_cache.get_value(
            variable_name='PROJECT_ACTION_SKIP_CONFIRMATION',
            value_if_expired=False,
            default_value_if_not_found=False,
            raise_exception_on_expired=False,
            raise_exception_on_not_found=False
        )
        if 'skipConfirmation' in self.spec:
            if isinstance(self.spec['skipConfirmation'], bool) is True:
                skip_confirmation = self.spec['skipConfirmation']
        variable_cache.store_variable(
            variable=Variable(
                name='PROJECT_ACTION_SKIP_CONFIRMATION',
                initial_value=skip_confirmation
            ),
            overwrite_existing=True
        )

        ###
        ### Process "manifestFiles" in Spec
        ###
        manifest_files = variable_cache.get_value(
            variable_name='PROJECT_MANIFEST_FILES',
            value_if_expired=list(),
            default_value_if_not_found=list(),
            raise_exception_on_expired=False,
            raise_exception_on_not_found=False
        )
        if 'manifestFiles' in self.spec:
            if isinstance(self.spec['manifestFiles'], list):
                for file in self.spec['manifestFiles']:
                    if file not in manifest_files:
                        manifest_files.append(file)
        variable_cache.store_variable(
            variable=Variable(
                name='PROJECT_MANIFEST_FILES',
                initial_value=manifest_files
            ),
            overwrite_existing=True
        )

        ###
        ### Process "extension_paths" in Spec
        ###
        extension_paths = variable_cache.get_value(
            variable_name='PROJECT_EXTENSION_PATHS',
            value_if_expired=list(),
            default_value_if_not_found=list(),
            raise_exception_on_expired=False,
            raise_exception_on_not_found=False
        )
        if 'extensionPaths' in self.spec:
            if isinstance(self.spec['extensionPaths'], list):
                for path in self.spec['extensionPaths']:
                    if path not in extension_paths:
                        extension_paths.append(path)
        variable_cache.store_variable(
            variable=Variable(
                name='PROJECT_EXTENSION_PATHS',
                initial_value=extension_paths
            ),
            overwrite_existing=True
        )
        
        action_state = Action.APPLY_DONE
        if actions.command == 'delete':
            action_state = Action.DELETE_DONE

        # If we reach this point, we are done
        actions.add_or_update_action(action=Action(manifest_kind=self.kind, manifest_name=self.metadata['name'], action_name='Project Action', action_status=action_state))
        return 

    def apply_manifest(self):
        for action_name, expected_action in actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name']).items():
            if action_name == 'Project Action' and expected_action == Action.APPLY_PENDING:
                self._process_action()                
        logger.info('Project Applied')
        return
    
    def delete_manifest(self):
        for action_name, expected_action in actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name']).items():
            if action_name == 'Project Action' and expected_action == Action.DELETE_PENDING:
                self._process_action()
        logger.info('Project Deleted')
        return

