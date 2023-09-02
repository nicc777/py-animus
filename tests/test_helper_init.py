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
from http.server import BaseHTTPRequestHandler, HTTPServer
import _thread as thread
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
print('sys.path={}'.format(sys.path))

import unittest


from py_animus.helpers import *

class TestFunctionGetUtcTimestamp(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)

    def tearDown(self):
        pass

    def test_get_int_time_01(self):
        result = get_utc_timestamp()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, int)
        self.assertTrue(result > 0)

    def test_get_int_time_02(self):
        result = get_utc_timestamp(with_decimal=False)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, int)
        self.assertTrue(result > 0)

    def test_get_float_time_01(self):
        result = get_utc_timestamp(with_decimal=True)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, float)
        self.assertTrue(result > 0.1)


class TestFunctionIsUrlAGitRepo(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)

    def tearDown(self):
        pass

    def test_positive_git_repo(self):
        result = is_url_a_git_repo(url='https://github.com/nicc777/py-animus')
        self.assertIsNotNone(result)
        self.assertIsInstance(result, bool)
        self.assertTrue(result)

    def test_negative_git_repo(self):
        result = is_url_a_git_repo(url='https://en.wikipedia.org/wiki/Python_(programming_language)')
        self.assertIsNotNone(result)
        self.assertIsInstance(result, bool)
        self.assertFalse(result)

    def test_positive_git_repo_with_zero_pads(self):
        result = is_url_a_git_repo(url='https://github.com/nicc777/py-animus{}00abc'.format('%'))
        self.assertIsNotNone(result)
        self.assertIsInstance(result, bool)
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
