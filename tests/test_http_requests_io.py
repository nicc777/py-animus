"""
    Copyright (c) 2022-2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import sys
import os
import tempfile
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
print('sys.path={}'.format(sys.path))

import unittest


from py_animus.utils.http_requests_io import *


class TestClassMainBasic01(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)
        self.tmp_dir = tempfile.TemporaryDirectory()
        print('TEMP DIR: {}'.format(self.tmp_dir.name))
        self.test_file_url = 'https://raw.githubusercontent.com/nicc777/py-animus/main/LICENSE'

    def tearDown(self):
        pass

    def test_basic_file_download(self):
        result = download_files(urls=[self.test_file_url], target_dir=self.tmp_dir.name)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result), 1)
        file = result[0]
        content = ''
        with open(file, 'r') as f:
            content = f.read()
        self.assertTrue('GNU GENERAL PUBLIC LICENSE' in content)

    def test_basic_file_download_not_verify_ssl(self):
        result = download_files(urls=[self.test_file_url], target_dir=self.tmp_dir.name, set_no_verify_ssl=True)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result), 1)
        file = result[0]
        content = ''
        with open(file, 'r') as f:
            content = f.read()
        self.assertTrue('GNU GENERAL PUBLIC LICENSE' in content)


if __name__ == '__main__':
    unittest.main()
