"""
    Copyright (c) 2022-2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
print('sys.path={}'.format(sys.path))

import unittest
import time


from py_animus.plugins import *
from py_animus import get_logger, parse_yaml_file


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


def my_post_parsing_method(params):
    print('Working with parameters: {}'.format(params))
    return

class MyManifest1(ManifestBase):

    def __init__(self, logger=get_logger(), post_parsing_method: object = my_post_parsing_method):
        super().__init__(logger, post_parsing_method)
        self.version = 'v0.1'
        self.supported_versions = [self.version,]

    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function)->bool:
        return True # We are always different

    def apply_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function):
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

def manifest_lookup_that_always_returns_MyManifest1(name: str):
    m = MyManifest1(post_parsing_method=my_post_parsing_method)
    m.parse_manifest(manifest_data=parse_yaml_file(yaml_data=my_manifest_1_data)['part_1'])
    return m


class TestMyManifest1(unittest.TestCase):    # pragma: no cover

    def test_init_with_defaults(self):
        result = manifest_lookup_that_always_returns_MyManifest1(name='dummy')
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

    def test_init_with_invalid_yaml_kind_throws_excaption(self):
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
        m.parse_manifest(manifest_data=parse_yaml_file(yaml_data=invalid_manifest_data)['part_1'])
        self.assertFalse(m.initialized)
        with self.assertRaises(Exception) as context:
            str(m)
        self.assertTrue('Class not yet fully initialized' in str(context.exception))

    def test_init_with_missing_kind_throws_excaption(self):
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
            m.parse_manifest(manifest_data=parse_yaml_file(yaml_data=invalid_manifest_data)['part_1'])
        self.assertTrue('Kind property not present in data' in str(context.exception))


if __name__ == '__main__':
    unittest.main()
