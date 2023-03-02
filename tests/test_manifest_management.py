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
import time


from py_animus.manifest_management import *
from py_animus import get_logger, parse_raw_yaml_data

running_path = os.getcwd()
print('Current Working Path: {}'.format(running_path))

class TestClassVariable(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)

    def test_init_with_defaults(self):
        result = Variable(name='test')
        self.assertIsNotNone(result)
        self.assertIsInstance(result, Variable)

    def test_method_set_value(self):
        v = Variable(name='test')
        v.set_value(value='test_value')
        self.assertIsNotNone(v.value)
        self.assertIsInstance(v.value, str)

        result = v.get_value()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertEqual(result, 'test_value')

        v.set_value(value=123)
        self.assertIsNotNone(v.value)
        self.assertIsInstance(v.value, int)

        result = v.get_value()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, int)
        self.assertEqual(result, 123)

    def test_init_with_short_ttl_no_exception(self):
        v = Variable(name='test', ttl=1)
        v.set_value(value='test_value')
        interim_result = v.get_value()
        self.assertIsNotNone(interim_result)
        self.assertIsInstance(interim_result, str)
        self.assertEqual(interim_result, 'test_value')

        time.sleep(2.0)
        result = v.get_value(value_if_expired='another_value', raise_exception_on_expired=False)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertEqual(result, 'another_value')

    def test_init_with_short_ttl_throw_exception(self):
        v = Variable(name='test', ttl=1)
        v.set_value(value=123, reset_ttl=False)
        time.sleep(2)
        with self.assertRaises(Exception) as context:
            v.get_value()
        self.assertTrue('Expired' in str(context.exception))

    def test_init_with_short_ttl_reset_timers_on_get_value(self):
        v = Variable(name='test', ttl=4)
        v.set_value(value='test_value')
        time.sleep(2)
        result = v.get_value(reset_timer_on_value_read=True)
        time.sleep(3)
        result = v.get_value(reset_timer_on_value_read=True)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertEqual(result, 'test_value')
        time.sleep(5)
        with self.assertRaises(Exception) as context:
            v.get_value()
        self.assertTrue('Expired' in str(context.exception))


class TestClassVariableCache(unittest.TestCase):    # pragma: no cover

    def test_init_with_defaults(self):
        result = VariableCache()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, VariableCache)

    def test_method_store_variable(self):
        vc = VariableCache()
        vc.store_variable(variable=Variable(name='test', initial_value=123))
        result = vc.get_value(variable_name='test')
        self.assertIsNotNone(result)
        self.assertIsInstance(result, int)
        self.assertEqual(result, 123)

    def test_method_get_non_existing_variable_fail_with_exception(self):
        vc = VariableCache()
        vc.store_variable(variable=Variable(name='test', initial_value=123))
        with self.assertRaises(Exception) as context:
            vc.get_value(variable_name='i_dont_exist')
        self.assertTrue('Variable "i_dont_exist" not found' in str(context.exception))

    def test_method_store_variables_dump_as_str(self):
        vc = VariableCache()
        vc.store_variable(variable=Variable(name='test1', initial_value=123))
        vc.store_variable(variable=Variable(name='test2', initial_value=456, ttl=60))
        result = str(vc)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)

        print('='*80)
        print('# test_method_store_variables_dump_as_str JSON')
        print(result)
        print('='*80)

        data_result = json.loads(result)
        self.assertIsNotNone(data_result)
        self.assertIsInstance(data_result, dict)
        self.assertTrue('test1' in data_result)
        self.assertTrue('test2' in data_result)
        self.assertIsNotNone(data_result['test1'])
        self.assertIsInstance(data_result['test1'], dict)
        self.assertIsNotNone(data_result['test2'])
        self.assertIsInstance(data_result['test2'], dict)
        self.assertTrue('ttl' in data_result['test1'])
        self.assertTrue('value' in data_result['test1'])
        self.assertTrue('expires' in data_result['test1'])
        self.assertTrue('ttl' in data_result['test2'])
        self.assertTrue('value' in data_result['test2'])
        self.assertTrue('expires' in data_result['test2'])


def my_post_parsing_method(**params):
    print('Working with parameters: {}'.format(params))
    return

class MyManifest1(ManifestBase):

    def __init__(self, logger=get_logger(), post_parsing_method: object = my_post_parsing_method, version: str='v0.1', supported_versions: tuple=('v0.1',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function)->bool:
        return True # We are always different

    def apply_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache()):
        variable_cache.store_variable(variable=Variable(name='{}:{}'.format(self.kind, self.metadata['name']), initial_value='Some Result Worth Saving'))
        return  # Assume some implementation
    

my_manifest_1_data=  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1
spec:
    val: 1
    more:
    - one
    - two
    - three
"""

def manifest_lookup_that_always_returns_MyManifest1(name: str)->ManifestBase:
    m = MyManifest1(post_parsing_method=my_post_parsing_method)
    m.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=my_manifest_1_data)['part_1'])
    if name == m.metadata['name']:
        return m
    raise Exception('Wrong Name!')


class MyManifest2(ManifestBase):

    def __init__(self, logger=get_logger(), post_parsing_method: object = my_post_parsing_method, version: str='v0.2', supported_versions: tuple=('v0.2',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function)->bool:
        return True # We are always different

    def apply_manifest(self, manifest_lookup_function: object=manifest_lookup_that_always_returns_MyManifest1, variable_cache: VariableCache=VariableCache()):
        m1 = manifest_lookup_function(name=self.spec['parent'])
        m1.apply_manifest(variable_cache=variable_cache)
        variable_cache.store_variable(variable=Variable(name='{}:{}'.format(self.kind, self.metadata['name']), initial_value='Another value worth storing'))
        return  # Assume some implementation


my_manifest_2_data=  """---
kind: MyManifest2
version: v0.2
metadata:
    name: test2
spec:
    val: 2
    parent: test1
"""


class TestMyManifest1(unittest.TestCase):    # pragma: no cover

    def test_init_with_defaults(self):
        result = manifest_lookup_that_always_returns_MyManifest1(name='test1')
        self.assertIsNotNone(result)
        self.assertIsInstance(result, MyManifest1)
        self.assertIsInstance(result, ManifestBase)

        yaml_result = str(result)
        self.assertIsNotNone(yaml_result)
        self.assertIsInstance(yaml_result, str)
        self.assertTrue(len(yaml_result) > 10)
        print('='*80)
        print('# test_init_with_defaults YAML')
        print(yaml_result)
        print('='*80)

    def test_init_with_invalid_yaml_kind_throws_exception(self):
        invalid_manifest_data =  """---
kind: SomeOtherUnsupportedKind
version: v0.1
metadata:
    name: test1
spec:
    val: 1
    more:
    - one
    - two
    - three"""
        m = MyManifest1(post_parsing_method=my_post_parsing_method)
        m.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=invalid_manifest_data)['part_1'])
        self.assertFalse(m.initialized)
        with self.assertRaises(Exception) as context:
            str(m)
        self.assertTrue('Class not yet fully initialized' in str(context.exception))

    def test_init_with_missing_kind_throws_exception(self):
        invalid_manifest_data =  """---
version: v0.1
metadata:
    name: test1
spec:
    val: 1
    more:
    - one
    - two
    - three"""
        m = MyManifest1(post_parsing_method=my_post_parsing_method)
        with self.assertRaises(Exception) as context:
            m.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=invalid_manifest_data)['part_1'])
        self.assertTrue('Kind property not present in data' in str(context.exception))

    def test_init_with_invalid_version_throws_exception(self):
        invalid_manifest_data =  """---
kind: MyManifest1
version: v0.2
metadata:
    name: test1
spec:
    val: 1
    more:
    - one
    - two
    - three"""
        m = MyManifest1(post_parsing_method=my_post_parsing_method)
        with self.assertRaises(Exception) as context:
            m.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=invalid_manifest_data)['part_1'])
        self.assertTrue('Version v0.2 not supported by this implementation' in str(context.exception))

    def test_init_with_version_not_present_throws_exception(self):
        invalid_manifest_data =  """---
kind: MyManifest1
metadata:
    name: test1
spec:
    val: 1
    more:
    - one
    - two
    - three"""
        m = MyManifest1(post_parsing_method=my_post_parsing_method)
        with self.assertRaises(Exception) as context:
            m.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=invalid_manifest_data)['part_1'])
        self.assertTrue('Version property not present in data.' in str(context.exception))

    def test_init_with_no_metadata_name_uses_default_name(self):
        manifest_data =  """---
kind: MyManifest1
version: v0.1
spec:
    val: 1
    more:
    - one
    - two
    - three"""
        m = MyManifest1(post_parsing_method=my_post_parsing_method)
        m.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_data)['part_1'])

        yaml_result = str(m)
        self.assertIsNotNone(yaml_result)
        self.assertIsInstance(yaml_result, str)
        self.assertTrue(len(yaml_result) > 10)
        print('='*80)
        print('# test_init_with_no_metadata_name_uses_default_name YAML')
        print(yaml_result)
        print('='*80)
        self.assertTrue('name: MyManifest1' in yaml_result)


class TestMyManifest2(unittest.TestCase):    # pragma: no cover

    def test_init_with_defaults(self):
        m2 = MyManifest2(post_parsing_method=my_post_parsing_method)
        m2.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=my_manifest_2_data)['part_1'])
        vc = VariableCache()
        m2.apply_manifest(manifest_lookup_function=manifest_lookup_that_always_returns_MyManifest1, variable_cache=vc)
        self.assertEqual(len(vc.values), 2)
        self.assertTrue('MyManifest1:test1' in vc.values)
        self.assertTrue('MyManifest2:test2' in vc.values)
        self.assertEqual(vc.get_value(variable_name='MyManifest1:test1'), 'Some Result Worth Saving')
        self.assertEqual(vc.get_value(variable_name='MyManifest2:test2'), 'Another value worth storing')


class TestManifestManager(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('*'*80)
        if os.path.exists('/tmp/test_manifest_classes'):
            if os.path.isdir(s='/tmp/test_manifest_classes'):
                shutil.rmtree(path='/tmp/test_manifest_classes', ignore_errors=True)
        os.mkdir(path='/tmp/test_manifest_classes')
        os.mkdir(path='/tmp/test_manifest_classes/test1')
        os.mkdir(path='/tmp/test_manifest_classes/test2')
        with open('{}/tests/manifest_classes/test1.py'.format(running_path), 'r') as f1r:
            with open('/tmp/test_manifest_classes/test1/test1.py', 'w') as f1w:
                f1w.write(f1r.read())
                print('Copied "{}" to "/tmp/test_manifest_classes/test1/test1.py"'.format('{}/tests/manifest_classes/test1.py'.format(running_path)))
        with open('{}/tests/manifest_classes/test2.py'.format(running_path), 'r') as f2r:
            with open('/tmp/test_manifest_classes/test2/test2.py', 'w') as f2w:
                f2w.write(f2r.read())
                print('Copied "{}" to "/tmp/test_manifest_classes/test1/test1.py"'.format('{}/tests/manifest_classes/test2.py'.format(running_path)))
        print('PREP COMPLETED')
        print('~'*80)

    def tearDown(self):
        if os.path.exists('/tmp/test_manifest_classes'):
            if os.path.isdir(s='/tmp/test_manifest_classes'):
                shutil.rmtree(path='/tmp/test_manifest_classes', ignore_errors=True)

    def test_init_with_test_files(self):
        vc = VariableCache()
        mm = ManifestManager(variable_cache=vc)
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test1')
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test2')
        self.assertEqual(len(mm.manifest_class_register), 2)

        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=my_manifest_1_data)['part_1'])
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=my_manifest_2_data)['part_1'])
        self.assertEqual(len(mm.manifest_instances), 2)
        self.assertTrue('test1' in mm.manifest_instances)
        self.assertTrue('test2' in mm.manifest_instances)
        mm.apply_manifest(name='test2')
        self.assertEqual(len(vc.values), 2)
        self.assertTrue('MyManifest1:test1' in vc.values)
        self.assertTrue('MyManifest2:test2' in vc.values)
        self.assertEqual(vc.values['MyManifest1:test1'].value, 'Some Result Worth Saving')
        self.assertEqual(vc.values['MyManifest2:test2'].value, 'Another value worth storing')
        for k,v in vc.values.items():
            print('{}={}'.format(k,v.value))

        # Test exceptions
        with self.assertRaises(Exception) as context:
            mm.get_manifest_class_by_kind(kind='NotRegisteredKind')
        self.assertTrue('Manifest kind "NotRegisteredKind" not registered' in str(context.exception))

        with self.assertRaises(Exception) as context:
            mm.get_manifest_instance_by_name(name='does-not-exist')
        self.assertTrue('No manifest instance for "does-not-exist" found' in str(context.exception))


if __name__ == '__main__':
    unittest.main()
