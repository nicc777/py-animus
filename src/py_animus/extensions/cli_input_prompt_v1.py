"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

from py_animus.models import all_scoped_values, variable_cache, Action, actions, Variable
from py_animus.models.extensions import ManifestBase
from getpass import getpass


class CliInputPrompt(ManifestBase):
    """Allows to pause for user input

        Spec fields:

        | Field                          | Type     | Required | Default Value                               | Description                                                                                                                                                                                                                                     |
        |--------------------------------|----------|----------|---------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
        | `spec.promptText`              | str      | No       | NULL                                        | The text to display on screen                                                                                                                                                                                                                   |
        | `spec.promptCharacter`         | str      | No       | `> `                                        | The character for the actual prompt                                                                                                                                                                                                             |
        | `spec.valueExpires`            | bool     | No       | False                                       | If set to true, the value will expire after `spec.valueTTL` seconds                                                                                                                                                                             |
        | `spec.valueTTL`                | int      | No       | 60                                          | If `spec.valueExpires` is used, use this value to fine tune the exact timeout period in seconds                                                                                                                                                 |
        | `spec.convertEmptyInputToNone` | bool     | No       | True                                        | If input is empty, convert the final value to NoneType                                                                                                                                                                                          |
        | `spec.maskInput`               | bool     | No       | False                                       | If true, do not echo characters. This is suitable to ask for a password, for example                                                                                                                                                            |
        | `spec.containsCredentials`     | bool     | No       | False                                       | If true, set the for_logging=True parameter for the Variable                                                                                                                                                                                    |

    """

    def __init__(self, post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)
        self.extension_action_descriptions = (
            'CLI Prompt',
        )

    def _validate(self):
        if self.spec is None:
            self.spec = dict()
        if isinstance(self.spec, dict) is False:
            self.spec = dict()

        if variable_cache.get_value(
            variable_name=self._var_name(var_name='VALIDATED'),
            value_if_expired=False,
            default_value_if_not_found=False,
            raise_exception_on_expired=False,
            raise_exception_on_not_found=False
        ) is False:

            self.log(message='Not Yet Validated', level='debug')

            if 'promptText' not in self.spec:
                self.spec['promptText'] = ''
            else:
                if self.spec['promptText'] is None:
                    self.spec['promptText'] = ''
                if isinstance(self.spec['promptText'], str) is False:
                    self.spec['promptText'] = ''

            if 'containsCredentials' not in self.spec:
                self.spec['containsCredentials'] = False
            else:
                if self.spec['containsCredentials'] is None:
                    self.spec['containsCredentials'] = False
                if isinstance(self.spec['containsCredentials'], bool) is False:
                    self.spec['containsCredentials'] = False

            if 'promptCharacter' not in self.spec:
                self.spec['promptCharacter'] = '> '
            else:
                if self.spec['promptCharacter'] is None:
                    self.spec['promptCharacter'] = '> '
                if isinstance(self.spec['promptCharacter'], str) is False:
                    self.spec['promptCharacter'] = '> '
                if len(self.spec['promptCharacter']) > 64:
                    self.spec['promptCharacter'] = '> '

            if 'valueExpires' not in self.spec:
                self.spec['valueExpires'] = False
            else:
                if self.spec['valueExpires'] is None:
                    self.spec['valueExpires'] = False
                if isinstance(self.spec['valueExpires'], bool) is False:
                    self.spec['valueExpires'] = False

            if self.spec['valueExpires'] is True:
                if 'valueTTL' not in self.spec:
                    self.spec['valueTTL'] = '60'
                else:
                    if self.spec['valueTTL'] is None:
                        self.spec['valueTTL'] = '60'
                    if isinstance(self.spec['valueTTL'], str) is False:
                        self.spec['valueTTL'] = '60'
                    try:
                        int(self.spec['valueTTL'])
                    except:
                        self.spec['valueTTL'] = '60'

            if 'convertEmptyInputToNone' not in self.spec:
                self.spec['convertEmptyInputToNone'] = True
            else:
                if self.spec['convertEmptyInputToNone'] is None:
                    self.spec['convertEmptyInputToNone'] = True
                if isinstance(self.spec['convertEmptyInputToNone'], bool) is False:
                    self.spec['convertEmptyInputToNone'] = True

            if 'maskInput' not in self.spec:
                self.spec['maskInput'] = False
            else:
                if self.spec['maskInput'] is None:
                    self.spec['maskInput'] = False
                if isinstance(self.spec['maskInput'], bool) is False:
                    self.spec['maskInput'] = False

            self.log(message='Spec Validated', level='debug')
            variable_cache.store_variable(variable=Variable(name=self._var_name(var_name='VALIDATED'),initial_value=True), overwrite_existing=True)
        else:
            self.log(message='Already Validated', level='debug')

    def implemented_manifest_differ_from_this_manifest(self)->bool:
        self._validate()
        current_value = variable_cache.get_value(
            variable_name=self._var_name(var_name='CLI_INPUT_VALUE'),
            value_if_expired=None,
            default_value_if_not_found=None,
            raise_exception_on_expired=False,
            raise_exception_on_not_found=False
        )
        if current_value is None:
            return True
        return False
    
    def apply_manifest(self):
        self.log(message='APPLY CALLED', level='info')
            
        for action_name, expected_action in actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name']).items():
            if action_name == 'CLI Prompt' and expected_action != Action.APPLY_PENDING:
                self.log(message='   Apply action "{}" will not be done. Status: {}'.format(action_name, expected_action), level='info')
                return

        value = None
        self.log(message='variable_cache={}'.format(str(variable_cache)), level='debug')

        self.log(message='Getting value from USER', level='info')
        self.log(message='spec={}'.format(self.spec), level='debug')
        if self.spec['promptText'] is not None:
            print(self.spec['promptText'])
        if self.spec['maskInput'] is True:
            value = getpass(prompt=self.spec['promptCharacter'])
        else:
            value = input(self.spec['promptCharacter'])
        self.log(message='value={}'.format(value), level='debug')
        if value == '' and self.spec['convertEmptyInputToNone'] is True:
            value = None
        self.log(message='value={}'.format(value), level='debug')

        ttl = -1
        if self.spec['valueExpires'] is True:
            ttl = int(self.spec['valueTTL'])

        variable_cache.store_variable(
            variable=Variable(
                name=self._var_name(var_name='CLI_INPUT_VALUE'),
                initial_value=value,
                ttl=ttl,
                mask_in_logs=self.spec['containsCredentials']
            ),
            overwrite_existing=True
        )
        self.log(
            message='("{}") Input value "{}"'.format(
                self._var_name(var_name='CLI_INPUT_VALUE'),
                variable_cache.get_value(
                    variable_name=self._var_name(var_name='CLI_INPUT_VALUE'),
                    value_if_expired='',
                    default_value_if_not_found='',
                    raise_exception_on_expired=False,
                    raise_exception_on_not_found=False,
                    for_logging=True
                )
            ),
            level='info'
        )
        actions.add_or_update_action(action=Action(manifest_kind=self.kind, manifest_name=self.metadata['name'], action_name='CLI Prompt', action_status=Action.APPLY_DONE))
        return

    def delete_manifest(self):
        self.log(message='DELETE CALLED - Rerouting to APPLY ACTION.', level='info')

        for action_name, expected_action in actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name']).items():
            if action_name == 'CLI Prompt' and expected_action != Action.DELETE_PENDING:
                self.log(message='   Apply action "{}" will not be done. Status: {}'.format(action_name, expected_action), level='info')
                return
            
        self.apply_manifest()
        return
