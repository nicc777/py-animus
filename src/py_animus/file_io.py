"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import traceback
import os
import shutil
import tempfile
from pathlib import Path
import re
import hashlib
import random
import copy
from py_animus.utils import generate_random_string


"""
    Functions:

    | Function Name             | Functionality Description                                                                              |
    |---------------------------|--------------------------------------------------------------------------------------------------------|
    | read_text_file            | Read a text file                                                                                       |
    | read_large_text_file      | Read a large text file and call a callback function after a certain number of bytes has been read      |
    | create_directory          | Creates a directory                                                                                    |
    | create_temp_directory     | Creates a temporary directory                                                                          |
    | delete_directory          | Creates a directory                                                                                    |
    | delete_temp_directory     | Creates a temporary directory                                                                          |
    | list_files                | List files in a given directory, optionally recursively                                                |
    | copy_file                 | Copy a file to a destination path, with options how to handle situations where the file already exists |
    | file_checksum             | Calculate the checksum of a given file                                                                 |

"""


def read_text_file(path_to_file: str)->str:
    """Read the text from a text file

    Args:
        path_to_file: The full path and file

    Returns:
        A string with the content of the file

    Raises:
        None
    """
    content = ''
    with open(path_to_file, 'r') as f:
        content = f.read()
    return content

def read_large_text_file(path_to_file: str, callback_func: callable, chunk_size: int=8192)->str:
    """Read the text from a text file 

    After a certain number of bytes is read, call the `callback_func()` function. 

    The parameters the callback_func() must except are the following named parameters:

    * path_to_file: str
    * current_chunk_sequence_number: int
    * chunk_size: int
    * content: str
    * return_object: object

    Each time the callback function is called, the result will be captured in return_object which will be sent again on the next call to the callback function.

    Args:
        path_to_file: The full path and file
        callback_func: The callback function reference
        chunk_size: The chunk size to read

    Returns:
        None

    Raises:
        None
    """

    try:
        current_chunk_sequence_number = 0
        return_object = None
        with open(path_to_file, 'r') as f:
            while chunk := f.read(chunk_size):
                parameters = {
                    'path_to_file': path_to_file,
                    'current_chunk_sequence_number': current_chunk_sequence_number,
                    'chunk_size': len(chunk),
                    'content': chunk,
                    'return_object': return_object,
                }
                return_object = callback_func(**parameters)
                current_chunk_sequence_number += 1
    except:
        traceback.print_exc()


def create_directory(path: str):
    """Create a directory

    Args:
        path: The directory to create

    Returns:
        Boolean true if successful

    Raises:
        None
    """
    try:
        os.mkdir(path)
    except:
        traceback.print_exc()
        return False
    return True


def delete_directory(dir: str)->bool:
    try:
        os.remove(dir)
    except:    
        try:
            shutil.rmtree(dir)
        except:
            traceback.print_exc()
            return False
    return True


def create_temp_directory()->str:
    """Create a directory

    Args:
        None

    Returns:
        String to the directory that was created

    Raises:
        None
    """
    tmp_dir = None
    try:
        tmp_dir = '{}{}{}'.format(
            tempfile.gettempdir(), 
            os.sep,
            generate_random_string(length=32)
        )
        delete_directory(tmp_dir) # Ensure it does not exist
        os.mkdir(tmp_dir)
    except:
        traceback.print_exc()
    return tmp_dir


def get_file_size(file_path: str)->int:
    size = None
    try:
        size = os.path.getsize(filename=file_path)
    except:
        traceback.print_exc()
    return size


def calculate_file_checksum(file_path: str, checksum_algorithm: str='md5')->str:
    checksum = None
    try:
        if checksum_algorithm.lower().startswith('md5'):
            checksum = hashlib.md5(open(file_path,'rb').read()).hexdigest()
        elif checksum_algorithm.lower().startswith('sha256'):
            checksum = hashlib.sha256(open(file_path,'rb').read()).hexdigest()
    except:
        traceback.print_exc()
    return checksum


def list_files(directory: str, recurse: bool=False, include_size: bool=False, calc_md5_checksum: bool=False, calc_sha255_checksum: bool=False, progress_callback_function: callable=None, result: dict=dict())->dict:
    """List all files in a directory.

    Note that each flag that is set to true may have a negative effect on performance.

    The progress_callback_function(), if used, must return a dict and must accept the following keyword parameters:

    * current_root: str
    * current_result: dict

    The result dictionary will have the following structure, unless modified by the progress_callback_function() (if set):

        ```python
        {
            '/full/path/to/file1.txt': {
                'size': 123,                # Or None, if include_size was False
                'md5': 'abc...xyz',         # Or None, if calc_md5_checksum was False
                'sha256': 'abc...xyz',      # Or None, if calc_sha255_checksum was False
            },
            '/full/path/to/file2.txt': { ... },
        }
        ```

    Therefore, the dictionary keys are the files with their full paths.

    if the progress_callback_function() is set, the callback will be done after every 100 files, and one final call just before the final result is returned. The final call will have the `current_root` value set to None, indicating that it is the final call.

    Args:
        directory: (required) string with the directory to scan.
        recurse: (optional) boolean to dive into sub-directories.
        include_size: (optional) include the file size of each file in the result set
        calc_md5_checksum: (optional) include the MD5 checksum of the file
        calc_sha255_checksum: (optional) include the SHA256 checksum of the file
        progress_callback_function: (optional) if set, this function will periodically be called with the accumulated result
        result: (optional) dict that will ultimately also contain the final result. If progress_callback_function() is called, the result object will be passed and the returned result (if a dictionary) will replace the current result value

    Returns:
        Dictionary with the collected data, unless modified by the progress_callback_function() callback function

    Raises:
        None
    """
    file_scan_counter = 0
    try:
        for root, dirs, files in os.walk(directory):
            if recurse is True:
                for dir in dirs:
                    result = {
                        **result,
                        **list_files(
                            directory='{}{}{}'.format(root, os.sep, dir),
                            recurse=recurse,
                            include_size=include_size,
                            calc_md5_checksum=calc_md5_checksum,
                            calc_sha255_checksum=calc_sha255_checksum,
                            progress_callback_function=progress_callback_function,
                            result=copy.deepcopy(result)
                        )
                    }
            for file in files:
                if progress_callback_function is not None:
                    file_scan_counter += 1
                    if file_scan_counter > 100:
                        file_scan_counter = 0
                        try:
                            callback_params = {
                                'current_root': root,
                                'current_result': copy.deepcopy(result)
                            }
                            result = copy.deepcopy(progress_callback_function(**callback_params))
                        except:
                            traceback.print_exc()
                file_full_path = '{}{}{}'.format(root, os.sep, file)
                file_metadata = dict()
                file_metadata['size'] = None
                file_metadata['md5'] = None
                file_metadata['sha256'] = None
                if include_size is True:
                    file_metadata['size'] = get_file_size(file_path=file_full_path)
                if calc_md5_checksum is True:
                    file_metadata['md5'] = calculate_file_checksum(file_path=file_full_path, checksum_algorithm='md5')
                if calc_sha255_checksum is True:
                    file_metadata['sha256'] = calculate_file_checksum(file_path=file_full_path, checksum_algorithm='sha256')
                result[file_full_path] = copy.deepcopy(file_metadata)
    except:
        traceback.print_exc()
    if progress_callback_function is not None:
        try:
            callback_params = {
                'current_root': None,
                'current_result': copy.deepcopy(result)
            }
            result = copy.deepcopy(progress_callback_function(**callback_params))
        except:
            traceback.print_exc()
    return copy.deepcopy(result)


def copy_file(source_file_path: str, destination_directory: str, new_name: str=None)->str:
    """Copy a file

    Args:
        source_file_path: (required) string containing the full path of the source file, for example `/path/to/file.txt`
        destination_directory: (required) string containing the destination directory only. By default, the source file name will be used as the target filename
        new_name: (optional) string that will be the final filename, if set

    Returns:
        String with the final full path of the destination file, if the copy was successful. May return None which may indicate failure.

    Raises:
        None
    """
    try:
        parts = source_file_path.split(os.sep)
        source_file_name = parts[-1]
        final_destination = '{}{}'.format(destination_directory, os.sep)
        if new_name is not None:
            final_destination = '{}{}'.format(final_destination, new_name)
        else:
            final_destination = '{}{}'.format(final_destination, source_file_name)
        shutil.copyfile(source_file_path, final_destination)
        return final_destination
    except:
        traceback.print_exc()
        return None

