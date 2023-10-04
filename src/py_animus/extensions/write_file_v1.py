"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

from py_animus.models import all_scoped_values, variable_cache, Action, actions, Variable
from py_animus.models.extensions import ManifestBase
from py_animus.helpers.file_io import *
import os
import stat


class WriteFile(ManifestBase):
    """This manifest will take provided data and write it to a file. The file can be (optionally) marked as executable.

The `apply` action will create the file and the `delete` action will delete the file. To retain files on `delete`
action, set the manifest skip option in the meta data.

The following variables will be defined:

* `FILE_PATH` - The full path to the file
* `WRITTEN` - Boolean, where a TRUE value means the file was processed.
* `EXECUTABLE` - Boolean value which will be TRUE if the file has been set as executable
* `SIZE` - The file size in BYTES
* `SHA256_CHECKSUM` - The calculated file checksum (SHA256)

Spec fields:

| Field                        | Type     | Required | Default Value  | Description                                                                                                                                 |
|------------------------------|----------|----------|----------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| `targetFile`                 | str      | Yes      | n/a            | Full path to a file                                                                                                                         |
| `data`                       | str      | Yes      | n/a            | The actual content of the file. Typically a `Value` or `Variable` reference will be used here                                               |
| `actionIfFileAlreadyExists`  | str      | No       | `overwrite`    | Allowed values: overwrite (write the data to the file anyway - overwriting any previous data), skip (leave the current file as is and skip) |
| `fileMode`                   | str      | No       | `normal`       | Allowed values: normal (chmod 600) or executable (chmod 700)                                                                                |
    """

    def __init__(self, post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)
        self.extension_action_descriptions = (
            'Write File',
        )

    def implemented_manifest_differ_from_this_manifest(self)->bool:
        written_before = variable_cache.get_value(
            variable_name=self._var_name(var_name='WRITTEN'),
            value_if_expired=False,
            default_value_if_not_found=False,
            raise_exception_on_expired=False,
            raise_exception_on_not_found=False
        )
        file_exists = os.path.exists(self.spec['targetFile'])

        action_if_exists = 'overwrite'
        if 'actionIfFileAlreadyExists' in self.spec:
            if self.spec['actionIfFileAlreadyExists'].lower() in ('overwrite', 'skip',):
                action_if_exists = self.spec['actionIfFileAlreadyExists'].lower()

        if written_before is False:
            if file_exists is True and action_if_exists == 'overwrite':
                return True

        if file_exists is False and written_before is False:
            return True

        return False

    def _set_variables(self):
        variable_cache.store_variable(
            variable=Variable(
                name=self._var_name(var_name='FILE_PATH'),
                initial_value=self.spec['targetFile'],
                mask_in_logs=False
            ),
            overwrite_existing=True
        )
        variable_cache.store_variable(
            variable=Variable(
                name=self._var_name(var_name='WRITTEN'),
                initial_value=True,
                mask_in_logs=False
            ),
            overwrite_existing=True
        )
        variable_cache.store_variable(
            variable=Variable(
                name=self._var_name(var_name='EXECUTABLE'),
                initial_value=os.access(self.spec['targetFile'], os.X_OK),
                mask_in_logs=False
            ),
            overwrite_existing=True
        )
        variable_cache.store_variable(
            variable=Variable(
                name=self._var_name(var_name='SIZE'),
                initial_value=get_file_size(file_path=self.spec['targetFile']),
                mask_in_logs=False
            ),
            overwrite_existing=True
        )
        variable_cache.store_variable(
            variable=Variable(
                name=self._var_name(var_name='SHA256_CHECKSUM'),
                initial_value=calculate_file_checksum(file_path=self.spec['targetFile'], checksum_algorithm='sha256'),
                mask_in_logs=False
            ),
            overwrite_existing=True
        )

    def apply_manifest(self):
        self.log(message='APPLY CALLED', level='info')

        for action_name, expected_action in actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name']).items():
            if action_name == 'Write File' and expected_action != Action.APPLY_PENDING:
                self.log(message='   Apply action "{}" will not be done. Status: {}'.format(action_name, expected_action), level='info')
                return

        try:
            os.unlink(self.spec['targetFile'])
        except:
            pass
        with open(self.spec['targetFile'], 'w') as f:
            f.write(self.spec['data'])

        if 'fileMode' in self.spec:
            if self.spec['fileMode'].lower().startswith('ex'):
                st = os.stat(self.spec['targetFile'])
                os.chmod(self.spec['targetFile'], st.st_mode | stat.S_IEXEC)

        self._set_variables()

        return

    def delete_manifest(self):
        self.log(message='DELETE CALLED', level='info')

        for action_name, expected_action in actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name']).items():
            if action_name == 'Write File' and expected_action != Action.DELETE_PENDING:
                self.log(message='   Apply action "{}" will not be done. Status: {}'.format(action_name, expected_action), level='info')
                return

        try:
            os.unlink(self.spec['targetFile'])
        except:
            pass

        for var_name in ('FILE_PATH', 'WRITTEN', 'EXECUTABLE', 'SIZE', 'SHA256_CHECKSUM',):
            variable_cache.delete_variable(variable_name=self._var_name(var_name=var_name))    

        return
