"""
    Copyright (c) 2022-2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import sys
import os
import json
import tempfile
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
print('sys.path={}'.format(sys.path))

import unittest


from py_animus.animus import run_main

class TestClassMain(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.manifest_file = '{}{}test.yaml'.format(self.tmp_dir.name, os.sep)
        with open(self.manifest_file, 'w') as f:
            f.write('test')

    def tearDown(self):
        os.unlink(self.manifest_file)
        os.rmdir(self.tmp_dir.name)


    def test_basic_init(self):
        result = run_main(cli_parameter_overrides=['animus.py', 'apply', self.manifest_file, 'project', 'test-scope'])
        self.assertIsNotNone(result)
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
