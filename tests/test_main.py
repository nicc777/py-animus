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
from unittest.mock import patch
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
print('sys.path={}'.format(sys.path))

import unittest


from py_animus.animus import run_main
from py_animus.models import VariableCache, AllScopedValues, all_scoped_values, variable_cache, scope, ScopedValues, Value


host_name_01 = "localhost"
server_port_01 = 7999
example_project_manifest_01 = '{}{}examples/projects/simple-01/project-01.yaml'.format(
    os.path.dirname(os.path.realpath(__file__)),
    os.sep
)
example_project_manifest_01 = example_project_manifest_01.replace('/tests/', '/')


class TestHttpServerBasic(BaseHTTPRequestHandler):  # pragma: no cover
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        content = ''
        with open(example_project_manifest_01, 'r') as f:
            content = f.read()
        self.wfile.write(bytes('{}'.format(content), 'utf-8'))


class TestClassMainBasic01(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)
        self.tmp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        os.rmdir(self.tmp_dir.name)

    @classmethod
    def setUpClass(cls):
        cls.web_server_01 = HTTPServer((host_name_01, server_port_01), TestHttpServerBasic)
        print("Server started http://%s:%s" % (host_name_01, server_port_01))
        def start_server():
            cls.web_server_01.serve_forever()
        thread.start_new_thread(start_server, ())

    @classmethod
    def tearDownClass(cls):
        cls.web_server_01.server_close()

    def _verify_values(self):
        self.assertIsNotNone(all_scoped_values)
        self.assertIsInstance(all_scoped_values, AllScopedValues)
        self.assertIsNotNone(all_scoped_values.scoped_values_collection)
        value = all_scoped_values.find_scoped_values(scope=scope.value).find_value_by_name(name='project-1-log-level').value
        self.assertIsNotNone(value)
        self.assertIsInstance(value, str)
        self.assertTrue(value, 'debug')

    @patch.dict('os.environ', {'DEBUG': 'e'})
    def test_basic_init_from_local_file(self):
        result = run_main(cli_parameter_overrides=['animus.py', 'apply', example_project_manifest_01, 'project', 'sandbox1'])
        self.assertIsNotNone(result)
        self.assertTrue(result)
        self._verify_values()

    @patch.dict('os.environ', {'DEBUG': 'e'})
    def test_basic_init_from_http_server(self):
        result = run_main(cli_parameter_overrides=['animus.py', 'apply', 'http://{}:{}/'.format(host_name_01, server_port_01), 'project', 'sandbox1'])
        self.assertIsNotNone(result)
        self.assertTrue(result)
        self._verify_values()

    def test_basic_init_with_invalid_project_fail_raises_Exception(self):
        with self.assertRaises(Exception):
            run_main(cli_parameter_overrides=['animus.py', 'apply', '/path/to/emptiness/and/darkness', 'project', 'sandbox1']) 


if __name__ == '__main__':
    unittest.main()
