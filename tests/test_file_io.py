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

    def test_create_temp_dir_with_sub_dir(self):
        tmp_dir = create_temp_directory()
        sub_dir = '{}{}test1'.format(tmp_dir, os.sep)
        create_directory(path=sub_dir)
        print('test_create_temp_dir(): tmp_dir={}'.format(tmp_dir))
        self.assertIsNotNone(sub_dir)
        self.assertIsInstance(sub_dir, str)
        self.assertTrue(os.path.isdir(sub_dir))
        delete_directory(dir=tmp_dir)
        self.assertFalse(os.path.exists(tmp_dir))


class TestFileIoRemainingFunctions(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)
        self.tmp_dir = create_temp_directory()
        self.dir_setup_data = (
            {
                'dir': '{}{}dir1'.format(self.tmp_dir, os.sep),
                'files': [
                    {
                        'file1.txt': 'content {}'.format(generate_random_string(length=8)) # Total length = 8+8 = 16
                    },
                    {
                        'file2.txt': 'content {}'.format(generate_random_string(length=16)) # Total length = 8+16 = 24
                    },
                ],
            },
            {
                'dir': '{}{}dir2'.format(self.tmp_dir, os.sep),
                'files': [
                    {
                        'file3.txt': 'content {}'.format(generate_random_string(length=16)) 
                    },
                    {
                        'file4.txt': 'content {}'.format(generate_random_string(length=32)) 
                    },
                ],
            },
            {
                'dir': '{}{}dir1{}subdir1'.format(self.tmp_dir, os.sep, os.sep),
                'files': [
                    {
                        'file5.txt': 'content {}'.format(generate_random_string(length=12)) 
                    },
                    {
                        'file6.txt': 'content {}'.format(generate_random_string(length=22)) 
                    },
                    {
                        'file7.txt': 'content {}'.format(generate_random_string(length=32)) 
                    },
                    {
                        'file8.txt': 'content {}'.format(generate_random_string(length=42)) 
                    },
                ],
            },
            {
                'dir': '{}{}dir1{}subdir2'.format(self.tmp_dir, os.sep, os.sep),
                'files': [
                    {
                        'file9.txt': 'content {}'.format(generate_random_string(length=52)) 
                    },
                    {
                        'file10.txt': 'content {}'.format(generate_random_string(length=62)) 
                    },
                ],
            },
            {
                'dir': '{}{}dir2{}subdir3'.format(self.tmp_dir, os.sep, os.sep),
                'files': [],
            },
            {
                'dir': '{}{}dir2{}subdir3{}subdir4'.format(self.tmp_dir, os.sep, os.sep, os.sep),
                'files': [
                    {
                        'file11.txt': 'content {}'.format(generate_random_string(length=72)) 
                    },
                    {
                        'file12.txt': 'content {}'.format(generate_random_string(length=82)) 
                    },
                    {
                        'file13.txt': 'content {}'.format(generate_random_string(length=92)) 
                    },
                ],
            },
        )
        print('PREPARING DIRECTORIES AND FILES')
        for dir in self.dir_setup_data:
            for dir_name, file_data in dir.items():
                create_directory(path=dir_name)
                print('* Created directory "{}"'.format(dir_name))
        
    def tearDown(self):
        print('DELETING DIRECTORIES')
        for dir in self.dir_setup_data:
            for dir_name, file_data in dir.items():
                delete_directory(dir=dir_name)
                print('* Deleted directory "{}"'.format(dir_name))

    



if __name__ == '__main__':
    unittest.main()
