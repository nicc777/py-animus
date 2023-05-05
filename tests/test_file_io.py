"""
    Copyright (c) 2022-2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
print('sys.path={}'.format(sys.path))

import unittest


from py_animus.manifest_management import *
from py_animus.utils import *
from py_animus.file_io import *

running_path = os.getcwd()
print('Current Working Path: {}'.format(running_path))

class TestFileIoCreateDirs(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)

    def test_create_temp_dir(self):
        tmp_dir = create_temp_directory()
        print('test_create_temp_dir(): tmp_dir={}'.format(tmp_dir))
        self.assertIsNotNone(tmp_dir)
        self.assertIsInstance(tmp_dir, str)
        self.assertTrue(os.path.isdir(tmp_dir))
        delete_directory(dir=tmp_dir)
        self.assertFalse(os.path.exists(tmp_dir))



if __name__ == '__main__':
    unittest.main()
