"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

from py_animus.models import all_scoped_values, variable_cache, Action, actions, Variable
from py_animus.models.extensions import ManifestBase
from py_animus.helpers.file_io import *
# from py_animus.manifest_management import *
# from py_animus import get_logger, get_utc_timestamp
from git import Repo


class GitRepo(ManifestBase):
    """Defines a Git repository.

Running `apply` will clone the Git repository to a local working directory and checkout the default or selected
branch.

If the work directory exists, it will first be deleted in order to clone a fresh copy of the selected repository.

The `delete` action will simply remove the working directory.

The following variables will be set and can be referenced in other manifests using [variable substitution](https://github.com/nicc777/py-animus/blob/main/doc/placeholder_values.md#variables-and-manifest-dependencies)

* `GIT_DIR` - Path to the working directory
* `BRANCH` - The branch checked out

Spec fields:

| Field                                                | Type     | Required | Default Value  | Description                                                                                                                                                                                                                                                                                                                            |
|------------------------------------------------------|----------|----------|----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `cloneUrl`                                           | str      | Yes      |                | The URL to the GIt repository to clone locally into the working directory                                                                                                                                                                                                                                                              |
| `authentication.type`                                | str      | No       |                | Must be either "http" or "ssh". If not supplied, no authentication will be used and the repository will be assumed to be public.                                                                                                                                                                                                       |
| `authentication.httpAuthentication.username`         | str      | No       |                | The username for HTTP(S) based Git repositories. Only required if `authentication.type` is set to `http`                                                                                                                                                                                                                               |
| `authentication.httpAuthentication.password`         | str      | No       |                | The password for HTTP(S) based Git repositories. Only required if `authentication.type` is set to `http`. Never put the actual password. See https://github.com/nicc777/py-animus/blob/main/doc/placeholder_values.md and https://github.com/nicc777/py-animus/blob/main/doc/placeholder_values.md#variables-and-manifest-dependencies |
| `authentication.sshAuthentication.sshPrivateKeyFile` | str      | No       |                | The full path to the SSH private key. Only required if `authentication.type` is set to `ssh`. For SSH this is for now the only supported option.                                                                                                                                                                                       |
| `workDir`                                            | str      | No       |                | If supplied, this directory will be used to clone the Git repository into. If not supplied, a random temporary directory will be created. The final value will be in the `GIT_DIR` variable.                                                                                                                                           |
| `checkoutBranch`                                     | str      | No       |                | If supplied, this branch will be checked out. Default=main                                                                                                                                                                                                                                                                             |
| `options.skipSslVerify`                              | bool     | No       |                | If `authentication.type` is `http` and there is a need to skip SSL verification, set this to `true`. Default=false                                                                                                                                                                                                                     |
        
    """

    def __init__(self, post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)
        self.extension_action_descriptions = (
            'Git Clone',
            'Git Pull'
        )

    def _create_temporary_working_directory(self)->str:
        work_dir = ''
        if 'workDir' in self.spec:
            work_dir = self.spec['workDir']
            delete_directory(dir=work_dir)
            create_directory(path=work_dir)
        else:
            work_dir = create_temp_directory()
        return work_dir

    def implemented_manifest_differ_from_this_manifest(self)->bool:
        work_dir = self._create_temporary_working_directory()
        variable_cache.store_variable(
            variable=Variable(
                name='{}:GIT_DIR'.format(self._var_name),
                initial_value=work_dir,
                logger=self.logger
            ),
            overwrite_existing=True
        )
        return True

    def _git_clone_from_https(
        self,
        url: str,
        username: str,
        password: str,
        skip_ssl: bool,
        target_dir: str,
        branch: str
    ):
        env = dict()
        if skip_ssl is True:
            env = dict(GIT_SSL_NO_VERIFY='1')
        if username is not None and password is not None:
            url_parts = url.split('/')
            url_parts[2] = '{}:{}@{}'.format(username,password,url_parts[2])
            url = '{}//{}'.format(url_parts[0], '/'.join(url_parts[2:]))
        Repo.clone_from(url=url, to_path=target_dir, env=env, branch=branch)

    def _git_clone_from_ssh(
        self,
        url: str,
        private_key: str,
        target_dir: str,
        branch: str
    ):
        env=dict(GIT_SSH_COMMAND='ssh -i {}'.format(private_key))
        self.log(message='_git_clone_from_ssh(): url         = {}'.format( url         ), level='debug')
        self.log(message='_git_clone_from_ssh(): private_key = {}'.format( private_key ), level='debug')
        self.log(message='_git_clone_from_ssh(): target_dir  = {}'.format( target_dir  ), level='debug')
        self.log(message='_git_clone_from_ssh(): branch      = {}'.format( branch      ), level='debug')
        Repo.clone_from(url=url, to_path=target_dir, env=env, branch=branch)

    def _get_branch(self)->str:
        branch = 'main'
        if 'checkoutBranch' in self.spec:
            if self.spec['checkoutBranch'] is not None:
                branch = '{}'.format(self.spec['checkoutBranch'])
        variable_cache.store_variable(
            variable=Variable(
                name='{}:BRANCH'.format(self._var_name),
                initial_value=branch,
                logger=self.logger
            ),
            overwrite_existing=True
        )
        return branch

    def _process_http_based_git_repo(self, branch: str):
        username = None
        password = None
        if 'authentication' in self.spec:
            if 'type' in self.spec['authentication']:
                if self.spec['authentication']['type'].lower().startswith('http') is True:
                    try:
                        username = self.spec['authentication']['httpAuthentication']['username']
                        password = self.spec['authentication']['httpAuthentication']['password']
                    except:
                        self.log(message='Failed to set username and password. Continuing with an attempt to clone anonymously.', level='warning')
        self._git_clone_from_https(
            url=self.spec['cloneUrl'].lower(),
            username=username,
            password=password,
            skip_ssl=False,
            target_dir=variable_cache.get_value(
                variable_name='{}:GIT_DIR'.format(self._var_name),
                raise_exception_on_expired=True,
                raise_exception_on_not_found=True
            ),
            branch=branch
        )

    def _process_other_git_repo(self, branch: str):
        if 'authentication' in self.spec:
            if 'type' in self.spec['authentication']:
                if self.spec['authentication']['type'].lower().startswith('ssh') is True:
                    private_key = None
                    try:
                        private_key = self.spec['authentication']['sshAuthentication']['sshPrivateKeyFile']
                    except:
                        self.log(message='PRIVATE KEY NOT SET - Attempting to clone repository anyway', level='warning')
                    if private_key is not None:
                        self._git_clone_from_ssh(
                            url=self.spec['cloneUrl'].lower(),
                            private_key=private_key,
                            target_dir=variable_cache.get_value(
                                variable_name='{}:GIT_DIR'.format(self._var_name),
                                raise_exception_on_expired=True,
                                raise_exception_on_not_found=True
                            ),
                            branch=branch
                        )
                    else:
                        self.log(message='Failed to clone Git repo - ssh repo without a private key cannot currently be cloned', level='error')
                else:
                    self.log(message='Failed to clone Git repo - Provided authentication type not recognized.', level='error')
            else:
                self.log(message='Failed to clone Git repo - Authentication type required but not present', level='error')
        else:
            self.log(message='Failed to clone Git repo - http not configured and unable to guess protocol and authentication method', level='error')

    def apply_manifest(self):
        self.log(message='APPLY CALLED', level='info')

        """
        2x Options possible:

            * 'Git Clone'
            * 'Git Pull'
        """
        final_action = None
        for action_name, expected_action in actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name']).items():
            if action_name == 'Git Clone' and expected_action != Action.APPLY_PENDING and final_action is None:
                self.log(message='   Apply action "{}" will not be done. Status: {}'.format(action_name, expected_action), level='info')
            elif action_name == 'Git Clone' and expected_action == Action.APPLY_PENDING and final_action is None:
                self.log(message='   Apply action "{}" will be done. Status: {}'.format(action_name, expected_action), level='info')
                final_action = 'Git Clone'
            elif action_name == 'Git Pull' and expected_action != Action.APPLY_PENDING and final_action is None:
                self.log(message='   Apply action "{}" will not be done. Status: {}'.format(action_name, expected_action), level='info')
            elif action_name == 'Git Pull' and expected_action == Action.APPLY_PENDING and final_action is None:
                self.log(message='   Apply action "{}" will be done. Status: {}'.format(action_name, expected_action), level='info')
                final_action = 'Git Pull'
        if final_action is None:
            return

        if final_action == 'Git Clone':
            branch = self._get_branch(variable_cache=variable_cache)
            if self.spec['cloneUrl'].lower().startswith('http') is True:
                self.log(message='Cloning a HTTP repository', level='info')
                self._process_http_based_git_repo(branch=branch, variable_cache=variable_cache)
            else:
                self.log(message='Cloning a SSH repository', level='info')
                self._process_other_git_repo(branch=branch, variable_cache=variable_cache)
        elif final_action == 'Git Pull':
            self.log(message='Git Pull action not yet implemented... For now you have to delete the existing Git repository first to ensure a fresh copy is cloned from source', level='warning')

        return

    def delete_manifest(self):
        self.log(message='DELETE CALLED', level='info')
        return
