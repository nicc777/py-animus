"""
    Copyright (c) 2022-2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import sys
import os
import json
import shutil
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
print('sys.path={}'.format(sys.path))

import unittest
from unittest import mock
import time


from py_animus.manifest_management import *
from py_animus import get_logger, parse_raw_yaml_data
from py_animus.py_animus import *

running_path = os.getcwd()
print('Current Working Path: {}'.format(running_path))

class TestPyAnimusMainMethod(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)
        if os.path.exists('/tmp/test_manifest_classes'):
            if os.path.isdir(s='/tmp/test_manifest_classes'):
                shutil.rmtree(path='/tmp/test_manifest_classes', ignore_errors=True)
        if os.path.exists('/tmp/test_manifests'):
            if os.path.isdir(s='/tmp/test_manifests'):
                shutil.rmtree(path='/tmp/test_manifests', ignore_errors=True)
        os.mkdir(path='/tmp/test_manifests')
        os.mkdir(path='/tmp/test_manifest_classes')
        os.mkdir(path='/tmp/test_manifest_classes/test1')
        os.mkdir(path='/tmp/test_manifest_classes/test2')

        self.source_to_dest_files = {
            # MyManifest1 versions
            '{}/tests/manifest_classes/test1v0-1.py'.format(running_path): '/tmp/test_manifest_classes/test1/test1v0-1.py',
            '{}/tests/manifest_classes/test1v0-2.py'.format(running_path): '/tmp/test_manifest_classes/test1/test1v0-2.py',
            '{}/tests/manifest_classes/test1v0-3.py'.format(running_path): '/tmp/test_manifest_classes/test1/test1v0-3.py',

            # MyManifest2 versions
            '{}/tests/manifest_classes/test2v0-1.py'.format(running_path): '/tmp/test_manifest_classes/test2/test2v0-1.py',
            '{}/tests/manifest_classes/test2v0-2.py'.format(running_path): '/tmp/test_manifest_classes/test2/test2v0-2.py',
            '{}/tests/manifest_classes/test2v0-3.py'.format(running_path): '/tmp/test_manifest_classes/test2/test2v0-3.py',
        }

        for source_file, dest_file in self.source_to_dest_files.items():
            with open(source_file, 'r') as f1r:
                with open(dest_file, 'w') as f1w:
                    f1w.write(f1r.read())
                    print('Copied "{}" to "{}"'.format(source_file, dest_file))

        
        manifest1_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-1
    environments:
    - env1
    - env2
    - env3
spec:
    val: '{}{} .Values.test1 {}{}'
""".format('{','{','}','}')

        manifest2_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-2
    environments:
    - env1
    - env2
spec:
    val: '{}{} .Values.test2 {}{}'
""".format('{','{','}','}')

        manifest3_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-3
    environments:
    - env2
    - env3
spec:
    val: '{}{} .Values.test3 {}{}'
""".format('{','{','}','}')
        
        manifests = {
            '/tmp/test_manifests/test1-1.yaml': manifest1_data,
            '/tmp/test_manifests/test1-2.yaml': manifest2_data,
            '/tmp/test_manifests/test1-3.yaml': manifest3_data,
        }

        for file, content in manifests.items():
            with open(file, 'w') as f:
                f.write(content)

        print('PREP COMPLETED')
        print('~'*80)

    def tearDown(self):
        if os.path.exists('/tmp/test_manifest_classes'):
            if os.path.isdir(s='/tmp/test_manifest_classes'):
                shutil.rmtree(path='/tmp/test_manifest_classes', ignore_errors=True)

    @mock.patch.dict(os.environ, {"DEBUG": "1"})   
    def test_main_with_defaults(self):
        cli_args=[
            'prog',
            'apply',
            '-m', '/tmp/test_manifests/test1-1.yaml',
            '-m', '/tmp/test_manifests/test1-2.yaml',
            '-m', '/tmp/test_manifests/test1-3.yaml',
            '-s', '/tmp/test_manifest_classes/test1/',
            '-s', '/tmp/test_manifest_classes/test2/',
            '-e', 'env3',
        ]
        vc = None
        mm = None
        with mock.patch.object(sys, 'argv', cli_args):
            vc, mm = run_main()
    
        self.assertIsNotNone(vc)
        self.assertIsInstance(vc, VariableCache)
        self.assertIsNotNone(mm)
        self.assertIsInstance(mm, ManifestManager)

        vc_data = vc.to_dict()
        print()
        print()
        print('vc={}'.format(json.dumps(vc_data)))
        print()
        print()

        # self.assertEqual(vc_data['MyManifest1:test1-1-val']['value'], 'val3')
        # self.assertEqual(vc_data['MyManifest1:test1-3-val']['value'], 'val9')


if __name__ == '__main__':
    unittest.main()