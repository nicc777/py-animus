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
