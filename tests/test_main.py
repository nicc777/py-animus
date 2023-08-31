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


from py_animus.animus import run_main


host_name_01 = "localhost"
server_port_01 = 7999


class TestHttpServerBasic(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(bytes("test", "utf-8"))


class TestClassMainBasic01(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.manifest_file = '{}{}test.yaml'.format(self.tmp_dir.name, os.sep)
        with open(self.manifest_file, 'w') as f:
            f.write('test')

    def tearDown(self):
        os.unlink(self.manifest_file)
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

    def test_basic_init_from_local_file(self):
        result = run_main(cli_parameter_overrides=['animus.py', 'apply', self.manifest_file, 'project', 'test-scope'])
        self.assertIsNotNone(result)
        self.assertTrue(result)

    def test_basic_init_from_http_server(self):
        result = run_main(cli_parameter_overrides=['animus.py', 'apply', 'http://{}:{}/'.format(host_name_01, server_port_01), 'project', 'test-scope'])
        self.assertIsNotNone(result)
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
