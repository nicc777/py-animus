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

    | Function Name      | Functionality Description | Return Type |
    |--------------------|---------------------------|-------------|
    | read_text_file     | Read a text file          | string      |
"""


def read_text_file(path_to_file: str)->str:
    """Read the text from a text file

    Args:
        path_to_file: The full path and file

    Returns:
        A string with the content of the file
    """
    content = ''
    with open(path_to_file, 'r') as f:
        content = f.read()
    return content