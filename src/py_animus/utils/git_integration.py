"""
    Copyright (c) 2022-2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import os
from git import Repo
import urllib
from py_animus.helpers.file_io import create_temp_directory, find_matching_files


def extract_parameters_from_url(
    location: str,
    branch: str='main',
    relative_start_directory: str='/',
    ssh_private_key_path: str=None,
    set_no_verify_ssl: bool=False
)->tuple:
    if '%00' in location:
        for item in urllib.parse.unquote_to_bytes(location).decode('utf-8').split('\x00'):
            if '=' in item:
                k, v = item.split('=')
                if k.lower() == 'branch':
                    branch = v
                elif k.lower() == 'relative_start_directory':
                    relative_start_directory = v
                elif k.lower() == 'ssh_private_key_path':
                    ssh_private_key_path = v
                elif k.lower() == 'set_no_verify_ssl':
                    if v.lower().startswith('t'):
                        set_no_verify_ssl = True
        location = location[0:location.find('%00')]
    return (
        location,
        branch,
        relative_start_directory,
        ssh_private_key_path,
        set_no_verify_ssl
    )


def git_clone_to_local(
    git_clone_url: str,
    branch: str='main',
    target_dir: str=None,
    ssh_private_key_path: str=None,
    set_no_verify_ssl: bool=False
)->str:
    """Clone a Git repository, and check out a branch

    Args:
        git_clone_url: A string containing the Git repository clone URL, for example `git@github.com:nicc777/verba-cratis-test-infrastructure.git`
        branch: String containing the branch name to check out. Default is `main`
        target_dir: A string containing the target directory. Default is `None` in which case a random temporary directory will be created and returned
        ssh_private_key_path: A string containing the SSH private key to use. Optional, and if value is `None`, the default transport (HTTPS) will be used.
        set_no_verify_ssl: A boolean that will not check SSL certificates if set to True (default=`False`). Useful when using self-signed certificates, but use with caution!!

    Returns:
        A string to the location of the cloned repository.

    Raises:
        Exception: In the event of an error
    """

    if '%00' in git_clone_url:
        git_clone_url = git_clone_url[0:git_clone_url.find('%00')]

    if target_dir is None:
        target_dir = create_temp_directory()

    if ssh_private_key_path is not None:
        git_ssh_cmd = 'ssh -i {}'.format(ssh_private_key_path)
        Repo.clone_from(url=git_clone_url, to_path=target_dir, env=dict(GIT_SSH_COMMAND=git_ssh_cmd), branch=branch)
    elif set_no_verify_ssl is True:
        Repo.clone_from(url=git_clone_url, to_path=target_dir, env=dict(GIT_SSL_NO_VERIFY='1'), branch=branch)
    else:
        Repo.clone_from(git_clone_url, target_dir, branch=branch)

    return target_dir


def git_clone_checkout_and_return_list_of_files(
    git_clone_url: str,
    branch: str='main',
    relative_start_directory: str='',
    include_files_regex: str='.*\.yaml$|.*\.yml$',
    target_dir: str='/tmp',
    ssh_private_key_path: str=None,
    set_no_verify_ssl: bool=False
)->list:
    """Parse files from a Git repository matching a file pattern withing a branch and directory to return a SystemConfigurations instance

    Args:
        git_clone_url: A string containing the Git repository clone URL, for example `git@github.com:nicc777/verba-cratis-test-infrastructure.git`
        branch: String containing the branch name to check out. Default is `main`
        relative_start_directory: String containing the sub-directory in the cloned repository to look for file. Default is the root of the cloned repository
        include_files_regex: A regular expression string for files to match. Default is matching YAML files.
        target_dir: A string containing the target directory for cloning the repository. Default is `None` in which case a random temporary directory will be created and returned
        ssh_private_key_path: A string containing the SSH private key to use. Optional, and if value is `None`, the default transport (HTTPS) will be used.
        set_no_verify_ssl: A boolean that will not check SSL certificates if set to True (default=`False`). Useful when using self-signed certificates, but use with caution!!

    Returns:
        A list of matching files

    Raises:
        Exception: In the event of an error
    """
    target_directory = git_clone_to_local(
        git_clone_url=git_clone_url,
        branch=branch,
        target_dir=target_dir,
        ssh_private_key_path=ssh_private_key_path,
        set_no_verify_ssl=set_no_verify_ssl
    )
    start_dir = target_directory
    if len(relative_start_directory) > 0:
        if relative_start_directory.startswith(os.sep):
            start_dir = '{}{}'.format(
                target_directory,
                relative_start_directory
            )
        else:
            start_dir = '{}{}{}'.format(
                target_directory,
                os.sep,
                relative_start_directory
            )
    return find_matching_files(start_dir=start_dir, pattern=include_files_regex)