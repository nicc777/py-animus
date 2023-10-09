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
| `options.skipSslVerify`                              | bool     | No       | False          | If `authentication.type` is `http` and there is a need to skip SSL verification, set this to `true`. Default=false                                                                                                                                                                                                                     |
        
    """

    def __init__(self, post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)
        self.extension_action_descriptions = (
            'Git Clone',
            'Git Pull',
            'Git Create Random Dir',
            'Git Delete Dir'
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
        # work_dir = self._create_temporary_working_directory()
        # variable_cache.store_variable(
        #     variable=Variable(
        #         name=self._var_name(var_name='GIT_DIR'),
        #         initial_value=work_dir,
        #         logger=self.logger
        #     ),
        #     overwrite_existing=True
        # )
        return True

    def determine_actions(self):
        if actions.command == 'delete':
            if 'skipDeleteAll' in self.metadata:
                if self.metadata['skipDeleteAll'] is True:
                    self._bulk_register_actions(final_action=Action.DELETE_SKIP)
                    return
        if actions.command == 'apply':
            if 'skipApplyAll' in self.metadata:
                if self.metadata['skipApplyAll'] is True:
                    self._bulk_register_actions(final_action=Action.APPLY_SKIP)
                    return
                
        if self.implemented_manifest_differ_from_this_manifest() is True:
            if actions.command == 'apply':
                if 'workDir' in self.spec:
                    if os.path.exists('{}{}.git'.format(self.metadata['workDirt'], os.sep)) is True:
                        self.register_action(action_name='Git Pull', initial_status=Action.APPLY_PENDING)
                        self.log(message='Registered action "Git Pull" with status "{}"'.format(Action.APPLY_PENDING), level='info')
                    else:
                        self.register_action(action_name='Git Clone', initial_status=Action.APPLY_PENDING)
                        self.log(message='Registered action "Git Clone" with status "{}"'.format(Action.APPLY_PENDING), level='info')    
                else:
                    self.register_action(action_name='Git Create Random Dir', initial_status=Action.APPLY_PENDING)
                    self.log(message='Registered action "Git Create Random Dir" with status "{}"'.format(Action.APPLY_PENDING), level='info')
                    self.register_action(action_name='Git Clone', initial_status=Action.APPLY_PENDING)
                    self.log(message='Registered action "Git Clone" with status "{}"'.format(Action.APPLY_PENDING), level='info')
            elif actions.command == 'delete':
                if 'workDir' in self.spec:
                    self.register_action(action_name='Git Delete Dir', initial_status=Action.APPLY_PENDING)
                    self.log(message='Registered action "Git Delete Dir" with status "{}"'.format(Action.APPLY_PENDING), level='info')
            else:
                raise Exception('Unknown or unsupported command for this manifest kind "{}"'.format(self.kind))
        else:
            # Right now we do not have a scenario where the implemented_manifest_differ_from_this_manifest() method will return false...
            self.log(message='Unforeseen scenario - no actions will be taken !!!', level='warning')
        return

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
                variable_name=self._var_name(var_name='GIT_DIR'),
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
                                variable_name=self._var_name(var_name='GIT_DIR'),
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

    def _process_git_pull(self):
        repo = Repo(
            variable_cache.get_value(
                variable_name=self._var_name(var_name='GIT_DIR'),
                raise_exception_on_expired=True,
                raise_exception_on_not_found=True
            )
        )
        o = repo.remotes.origin
        o.pull()
        repo.git.checkout(self._get_branch())

    def apply_manifest(self):
        self.log(message='APPLY CALLED', level='info')

        """
        2x Options possible:

            * 'Git Clone'
            * 'Git Pull'
        """
        final_actions = list()
        for action_name, expected_action in actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name']).items():
            if action_name == 'Git Clone' and expected_action != Action.APPLY_PENDING:
                self.log(message='   Apply action "{}" will not be done. Status: {}'.format(action_name, expected_action), level='info')
            elif action_name == 'Git Clone' and expected_action == Action.APPLY_PENDING:
                self.log(message='   Apply action "{}" will be done. Status: {}'.format(action_name, expected_action), level='info')
                final_actions.append('Git Clone')
            elif action_name == 'Git Pull' and expected_action != Action.APPLY_PENDING:
                self.log(message='   Apply action "{}" will not be done. Status: {}'.format(action_name, expected_action), level='info')
            elif action_name == 'Git Pull' and expected_action == Action.APPLY_PENDING:
                self.log(message='   Apply action "{}" will be done. Status: {}'.format(action_name, expected_action), level='info')
                final_actions.append('Git Pull')
            
            if action_name == 'Git Create Random Dir' and expected_action != Action.APPLY_PENDING:
                self.log(message='   Apply action "{}" will not be done. Status: {}'.format(action_name, expected_action), level='info')
            elif action_name == 'Git Create Random Dir' and expected_action == Action.APPLY_PENDING:
                self.log(message='   Apply action "{}" will be done. Status: {}'.format(action_name, expected_action), level='info')
                final_actions.append('Git Create Random Dir')

        if len(final_actions) == 0:
            return

        work_dir = None
        if 'Git Create Random Dir' in final_actions:
            work_dir = create_temp_directory()
            self.log(message='Created system generated working directory "{}"'.format(work_dir), level='info')
        else:
            work_dir = self.spec['workDir']
            if os.path.exists(work_dir) is False:
                create_directory(path=work_dir)
                self.log(message='Created working directory "{}"'.format(work_dir), level='info')
        self.log(message='Using working directory "{}"'.format(work_dir), level='info')

        if work_dir is not None:
            variable_cache.store_variable(
                variable=Variable(
                    name=self._var_name(var_name='GIT_DIR'),
                    initial_value=work_dir,
                    logger=self.logger
                ),
                overwrite_existing=True
            )
        else:
            raise Exception('Cannot proceed as work directory is not set...')

        if 'Git Clone' in final_actions:
            branch = self._get_branch(variable_cache=variable_cache)
            if self.spec['cloneUrl'].lower().startswith('http') is True:
                self.log(message='Cloning a HTTP repository', level='info')
                self._process_http_based_git_repo(branch=branch)
            else:
                self.log(message='Cloning a SSH repository', level='info')
                self._process_other_git_repo(branch=branch)
        elif 'Git Pull' in final_actions:
            self._process_git_pull()

        return

    def delete_manifest(self):
        self.log(message='DELETE CALLED', level='info')

        if 'workDir' in self.spec:
            pass

        return
