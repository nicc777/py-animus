"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

from py_animus.models import all_scoped_values, variable_cache, Action, actions, Variable
from py_animus.models.extensions import ManifestBase
import traceback
import subprocess
import tempfile
import chardet
import os


class ShellScript(ManifestBase):    # pragma: no cover    
    """
        Spec fields:

        | Field                        | Type     | Required | Default Value                               | Description                                                                                                                                                                                                                                     |
        |------------------------------|----------|----------|---------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|        
        | `shellInterpreter`           |  str     | No       | `sh`                                        | The shell interpreter to select in the shabang line. Supported values: `sh`, `zsh`, `perl`, `python` and `bash`                                                                                                                                 |
        | `source`                     |  dict    | Yes      | n/a                                         | Defines the script source                                                                                                                                                                                                                       |
        | `source.type`                |  str     | No       | `inline`                                    | Select the source type, which can be either `filePath` that points to an existing script file on the local file system, or `inLine` with the script source defined in the `spec.source.value` field                                             |
        | `source.value`               |  str     | No       | `exit 0`                                    | If `spec.source.type` has a value of `inLine` then the value here will be assumed to be the script content of that type. if `spec.source.type` has a value of `filePath` then this value must point to an existing file on the local filesystem |
        | `workDir.path`               |  str     | No       | System Generated                            | An optional path to a working directory. The extension will create temporary files (if needed) in this directory and execute them from here.                                                                                                    |
        | `convertOutputToText`        |  bool    | No       | False                                       | Normally the STDOUT and STDERR will be binary encoded. Setting this value to true will convert those values to a normal string. Default=False                                                                                                   |
        | `stripNewline`               |  bool    | No       | False                                       | Output may include newline or other line break characters. Setting this value to true will remove newline characters. Default=False                                                                                                             |
        | `convertRepeatingSpaces`     |  bool    | No       | False                                       | Output may contain more than one repeating space or tab characters. Setting this value to true will replace these with a single space. Default=False                                                                                            |
        | `stripLeadingTrailingSpaces` |  bool    | No       | False                                       | Output may contain more than one repeating space or tab characters. Setting this value to true will replace these with a single space. Default=False                                                                                            |

    """

    def __init__(self, post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)
        self.extension_action_descriptions = (
            'Run ShellScript',
        )

    def implemented_manifest_differ_from_this_manifest(self)->bool:
        current_exit_code = variable_cache.get_value(
            variable_name=self._var_name(var_name='EXIT_CODE'),
            value_if_expired=None,
            default_value_if_not_found=None,
            raise_exception_on_expired=False,
            raise_exception_on_not_found=False
        )
        self.log(message='      current_exit_code={}'.format(current_exit_code), level='debug')
        if current_exit_code is not None:
            self.log(message='      returning False', level='debug')
            return False
        self.log(message='      returning True', level='debug')
        return True

    def _id_source(self)->str:
        source = 'inline'
        if 'source' in self.spec:
            if 'type' in self.spec['source']:
                if self.spec['source']['type'] in ('inLine', 'filePath',):
                    source = self.spec['source']['type']
        return source

    def _load_source_from_spec(self)->str:
        source = 'exit 0'
        if 'source' in self.spec:
            if 'value' in self.spec['source']:
                source = self.spec['source']['value']
        return source

    def _load_source_from_file(self)->str:
        source = 'exit 0'
        if 'source' in self.spec:
            if 'value' in self.spec['source']:
                try:
                    self.log(message='   Loading script source from file "{}"'.format(self.spec['source']['value']), level='info')
                    with open(self.spec['source']['value'], 'r') as f:
                        source = f.read()
                except:
                    self.log(message='   EXCEPTION: {}'.format(traceback.format_exc()), level='error')
        return source

    def _get_work_dir(self)->str:
        work_dir = tempfile.gettempdir()
        if 'workDir' in self.spec:
            if 'path' in self.spec['workDir']:
                work_dir = self.spec['workDir']['path']
        self.log(message='   Workdir set to "{}"'.format(work_dir), level='info')
        return work_dir

    def _del_file(self, file: str):
        try:
            os.unlink(file)
        except:
            pass

    def _create_work_file(self, source:str)->str:
        work_file = '{}{}{}'.format(
            self._get_work_dir(),
            os.sep,
            self.metadata['name']
        )
        self.log(message='   Writing source code to file "{}"'.format(work_file), level='info')
        self._del_file(file=work_file)
        try:
            with open(work_file, 'w') as f:
                f.write(source)
            self.log(message='      DONE', level='info')
        except:
            self.log(message='   EXCEPTION in _create_work_file(): {}'.format(traceback.format_exc()), level='error')
        return work_file

    def __detect_encoding(self, input_str: str)->str:
        encoding = None
        try:
            encoding = chardet.detect(input_str)['encoding']
        except:
            pass
        return encoding

    def apply_manifest(self):
        self.log(message='APPLY CALLED', level='info')
            
        for action_name, expected_action in actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name']).items():
            if action_name == 'Run ShellScript' and expected_action != Action.APPLY_PENDING:
                self.log(message='   Apply action "{}" will not be done. Status: {}'.format(action_name, expected_action), level='info')
                return

        ###
        ### PREP SOURCE FILE
        ###
        script_source = 'exit 0'
        if self._id_source() == 'inline':
            shabang = '#!/bin/sh'
            if 'shellInterpreter' in self.spec:
                shabang = self.spec['shellInterpreter']
                script_source = '#!/usr/bin/env {}\n\n{}'.format(
                    shabang,
                    self._load_source_from_spec()
                )
            else:
                script_source = '{}\n\n{}'.format(
                    shabang,
                    self._load_source_from_spec()
                )
        else:
            script_source = self._load_source_from_file()
        self.log(message='script_source:\n--------------------\n{}\n--------------------'.format(script_source), level='debug')
        work_file = self._create_work_file(source=script_source)

        ###
        ### EXECUTE
        ###
        result = None
        try:
            os.chmod(work_file, 0o700)
            result = subprocess.run('{}'.format(work_file), check=True, capture_output=True)   # Returns CompletedProcess
        except:
            self.log(message='   EXCEPTION in apply_manifest(): {}'.format(traceback.format_exc()), level='error')
            self.log(message='   Storing Variables', level='info')
            try:
                self.log(message='      Storing Exit Code', level='info')
                variable_cache.store_variable(
                    variable=Variable(
                        name=self._var_name(var_name='EXIT_CODE'),
                        initial_value=-999
                    ),
                    overwrite_existing=True
                )
                self.log(message='      Storing STDOUT', level='info')
                variable_cache.store_variable(
                    variable=Variable(
                        name=self._var_name(var_name='STDOUT'),
                        initial_value=None
                    ),
                    overwrite_existing=True
                )
                self.log(message='      Storing STDERR', level='info')
                variable_cache.store_variable(
                    variable=Variable(
                        name=self._var_name(var_name='STDERR'),
                        initial_value=None
                    ),
                    overwrite_existing=True
                )
                self.log(message='      Storing ALL DONE', level='info')
            except:
                self.log(message='   EXCEPTION in apply_manifest() when storing variables: {}'.format(traceback.format_exc()), level='error')

        ###
        ### STORE VALUES
        ###
        if result is not None:
            self.log(message='   Storing Variables', level='info')
            try:
                self.log(message='      Storing Exit Code', level='info')
                value_stdout_encoding = self.__detect_encoding(input_str=result.stdout)
                value_stderr_encoding = self.__detect_encoding(input_str=result.stdout)
                value_stdout_final = result.stdout
                value_stderr_final = result.stderr
                variable_cache.store_variable(
                    variable=Variable(
                        name=self._var_name(var_name='EXIT_CODE'),
                        initial_value=result.returncode
                    ),
                    overwrite_existing=True
                )
                self.log(message='      Storing STDOUT', level='info')

                if 'convertOutputToText' in self.spec:
                    if self.spec['convertOutputToText'] is True:
                        if value_stdout_encoding is not None:
                            value_stdout_final = value_stdout_final.decode(value_stdout_encoding)
                        if value_stderr_encoding is not None:
                            value_stderr_final = value_stderr_final.decode(value_stderr_encoding)

                if 'stripNewline' in self.spec:
                    if self.spec['stripNewline'] is True:
                        try:
                            if value_stdout_final is not None:
                                value_stdout_final = value_stdout_final.replace('\n', '')
                                value_stdout_final = value_stdout_final.replace('\r', '')
                            if value_stderr_final is not None:
                                value_stderr_final = value_stderr_final.replace('\n', '')
                                value_stderr_final = value_stderr_final.replace('\r', '')
                        except:
                            traceback.print_exc()
                            self.log(message='Could not remove newline characters after "StripNewline" setting was set to True', level='warning')

                if 'convertRepeatingSpaces' in self.spec:
                    if self.spec['convertRepeatingSpaces'] is True:
                        try:
                            if value_stdout_final is not None:
                                value_stdout_final = ' '.join(value_stdout_final.split())
                            if value_stderr_final is not None:
                                value_stderr_final = ' '.join(value_stderr_final.split())
                        except:
                            traceback.print_exc()
                            self.log(message='Could not remove repeating whitespace characters after "ConvertRepeatingSpaces" setting was set to True', level='warning')

                if 'stripLeadingTrailingSpaces' in self.spec:
                    if self.spec['stripLeadingTrailingSpaces'] is True:
                        try:
                            if value_stdout_final is not None:
                                value_stdout_final = value_stdout_final.strip()
                            if value_stderr_final is not None:
                                value_stderr_final = value_stderr_final.strip()
                        except:
                            traceback.print_exc()
                            self.log(message='Could not remove repeating whitespace characters after "ConvertRepeatingSpaces" setting was set to True', level='warning')

                variable_cache.store_variable(
                    variable=Variable(
                        name=self._var_name(var_name='STDOUT'),
                        initial_value=value_stdout_final
                    ),
                    overwrite_existing=True
                )
                self.log(message='      Storing STDERR', level='info')
                variable_cache.store_variable(
                    variable=Variable(
                        name=self._var_name(var_name='STDERR'),
                        initial_value=value_stderr_final
                    ),
                    overwrite_existing=True
                )
                self.log(message='      Storing ALL DONE', level='info')
            except:
                self.log(message='   EXCEPTION in apply_manifest() when storing variables: {}'.format(traceback.format_exc()), level='error')
        return_code = variable_cache.get_value(variable_name=self._var_name(var_name='EXIT_CODE'), value_if_expired=None, default_value_if_not_found=None, raise_exception_on_expired=False, raise_exception_on_not_found=False)
        l = 'info'
        if return_code is not None:
            if isinstance(return_code, int):
                if return_code != 0:
                    l = 'error'
        self.log(message='Return Code: {}'.format(return_code), level=l)

        ###
        ### DONE
        ###
        self._del_file(file=work_file)
        actions.add_or_update_action(action=Action(manifest_kind=self.kind, manifest_name=self.metadata['name'], action_name='Run ShellScript', action_status=Action.APPLY_DONE))
        return

    def delete_manifest(self):
        self.log(message='DELETE CALLED - Rerouting to APPLY ACTION.', level='info')

        for action_name, expected_action in actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name']).items():
            if action_name == 'Run ShellScript' and expected_action != Action.DELETE_PENDING:
                self.log(message='   Apply action "{}" will not be done. Status: {}'.format(action_name, expected_action), level='info')
                return
            
        self.apply_manifest()
        return
