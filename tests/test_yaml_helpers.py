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


from py_animus.helpers.yaml_helper import * 
from py_animus.models import ScopedValues, Value
from py_animus.models.extensions import ManifestBase
from py_animus.models import all_scoped_values, variable_cache, Action, actions
from py_animus.extensions import extensions

running_path = os.getcwd()
print('Current Working Path: {}'.format(running_path))


class TestFunctionYamlFileHelpers(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.manifest_file = '{}{}test.yaml'.format(self.tmp_dir.name, os.sep)
        with open(self.manifest_file, 'w') as f:
            f.write('''---
kind: K1
version: 1
spec:
  name: test1
---
kind: K1
version: 1
spec:
  name: test2
---
kind: K2
version: 1
spec:
  name: test3
''')

    def tearDown(self):
        os.unlink(self.manifest_file)
        os.rmdir(self.tmp_dir.name)

    def test_function_get_kind_from_text_basic_multiline_with_kind_01(self):
        variations = (
            'kind: abc\nversion: 1\nspec:\n  test:123',
            'KIND: abc\nVERSION: 1\nSPEC:\n  TEST:123',
            'Kind: abc\nVersion: 1\nSpec:\n  Test:123',
            'kINd: abc\nversion: 1\nspec:\n  test:123',
            'kinD: abc\nversion: 1\nspec:\n  test:123',

            'version: 1\nkind: abc\nspec:\n  test:123',
            'VERSION: 1\nKIND: abc\nSPEC:\n  TEST:123',
            'Version: 1\nKind: abc\nSpec:\n  Test:123',
            'version: 1\nkINd: abc\nspec:\n  test:123',
            'version: 1\nkinD: abc\nspec:\n  test:123',

            'version: 1\nspec:\n  test:123\nkind: abc',
            'VERSION: 1\nSPEC:\n  TEST:123\nKIND: abc',
            'Version: 1\nSpec:\n  Test:123\nKind: abc',
            'version: 1\nspec:\n  test:123\nkINd: abc',
            'version: 1\nspec:\n  test:123\nkinD: abc',
        )
        for text in variations:
            kind = get_kind_from_text(text=text)
            self.assertIsNotNone(kind, 'Failed on text string "{}"'.format(text))
            self.assertIsInstance(kind, str, 'Failed on text string "{}"'.format(text))
            self.assertTrue(kind == 'abc', 'Failed on text string "{}"'.format(text))

    def test_function_spit_yaml_file_with_multiple_yaml_sections(self):
        yaml_sections = spit_yaml_text_from_file_with_multiple_yaml_sections(yaml_text=self.manifest_file)
        self.assertIsNotNone(yaml_sections)
        self.assertIsInstance(yaml_sections, dict)
        self.assertTrue('K1' in yaml_sections)
        self.assertTrue('K2' in yaml_sections)
        self.assertIsNotNone(yaml_sections['K1'])
        self.assertIsNotNone(yaml_sections['K2'])
        self.assertIsInstance(yaml_sections['K1'], list)
        self.assertIsInstance(yaml_sections['K2'], list)
        self.assertEqual(len(yaml_sections['K1']), 2)
        self.assertEqual(len(yaml_sections['K2']), 1)


class MockManifestExtension(ManifestBase):
    
    def __init__(self, post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def implemented_manifest_differ_from_this_manifest(self)->bool:
        return True
    
    def determine_actions(self)->list:
        self.register_action(action_name='MockManifestExtension', initial_status=Action.UNKNOWN)
        if self.implemented_manifest_differ_from_this_manifest() is True:
            self.register_action(action_name='MockManifestExtension', initial_status=Action.APPLY_PENDING)
        return actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name'])
    
    def apply_manifest(self): 
        return
    
    def delete_manifest(self):
        return
    

extensions.add_extension(extension=MockManifestExtension)


class TestClassValueTag(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)
        scope.set_scope(new_value='test-scope')
        scoped_values = ScopedValues(scope='test-scope')
        scoped_values.add_value(value=Value(name='test-value-1', initial_value='test-string-1'))
        all_scoped_values.add_scoped_values(scoped_values=scoped_values, replace=True)
        self.test_yaml = '''kind: MockManifestExtension
version: v1
metadata:
  name: test
  environments:
  - test-scope
spec:
  finalValue: !Value test-value-1
'''

    def test_basic_parsing(self):
        test_extension_class = parse_animus_formatted_yaml(raw_yaml_str=self.test_yaml)
        self.assertIsNotNone(test_extension_class)
        self.assertIsInstance(test_extension_class, MockManifestExtension)

        print('Final Data:')
        print('-----------')
        print(str(test_extension_class))
        print('-----------')

        self.assertTrue(test_extension_class.spec['finalValue'] == 'test-string-1')
    


if __name__ == '__main__':
    unittest.main()
