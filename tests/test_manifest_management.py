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

    def test_masking_of_string(self):
        v = Variable(name='test', mask_in_logs=True)
        v.set_value(value='i-am-sensitive', reset_ttl=False)
        result = v.get_value(for_logging=True)
        self.assertEqual(result, '**************')

    def test_masking_of_int(self):
        v = Variable(name='test', mask_in_logs=True)
        v.set_value(value=123456789, reset_ttl=False)
        result = v.get_value(for_logging=True)
        self.assertEqual(result, '***')


class TestClassVariableCache(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)
    
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

    def test_method_delete_variable(self):
        vc = VariableCache()
        vc.store_variable(variable=Variable(name='test1', initial_value=123))
        vc.store_variable(variable=Variable(name='test2', initial_value=456))
        vc.store_variable(variable=Variable(name='test3', initial_value=789))
        vc.delete_variable(variable_name='test2')
        vc.delete_variable(variable_name='test4')   # No material effect
        
        vc_str = str(vc)
        print('='*80)
        print('# test_method_delete_variable JSON')
        print(vc_str)
        print('='*80)

        self.assertEqual(len(vc.values), 2)
        self.assertTrue('test1' in vc.values)
        self.assertFalse('test2' in vc.values)
        self.assertTrue('test3' in vc.values)

    def test_masking_of_string(self):
        vc = VariableCache()
        v = Variable(name='test', mask_in_logs=True)
        v.set_value(value='i-am-sensitive', reset_ttl=False)
        vc.store_variable(variable=v)
        result = vc.get_value(variable_name='test', for_logging=True)
        self.assertEqual(result, '**************')

    def test_masking_of_int(self):
        vc = VariableCache()
        v = Variable(name='test', mask_in_logs=True)
        v.set_value(value=123456789, reset_ttl=False)
        vc.store_variable(variable=v)
        result = vc.get_value(variable_name='test', for_logging=True)
        self.assertEqual(result, '***')


def my_post_parsing_method(**params):
    print('Working with parameters: {}'.format(params))
    return

class MyManifest1(ManifestBase):

    def __init__(self, logger=get_logger(), post_parsing_method: object = my_post_parsing_method, version: str='v0.1', supported_versions: tuple=('v0.1',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders())->bool:
        return True # We are always different

    def apply_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders()):
        self.log(message='MANIFEST: {}'.format(json.dumps(self.to_dict())), level='info')
        variable_cache.store_variable(variable=Variable(name='{}:{}'.format(self.kind, self.metadata['name']), initial_value='Some Result Worth Saving'))
        variable_cache.store_variable(variable=Variable(name='{}:{}-val'.format(self.kind, self.metadata['name']), initial_value=self.spec['val']), overwrite_existing=True)
        variable_cache.store_variable(variable=Variable(name='{}:{}-applied'.format(self.kind, self.metadata['name']), initial_value=True), overwrite_existing=True)
        variable_cache.store_variable(variable=Variable(name='{}:{}-deleted'.format(self.kind, self.metadata['name']), initial_value=False), overwrite_existing=True)
        return  # Assume some implementation
    
    def delete_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders()):
        self.log(message='MANIFEST: {}'.format(json.dumps(self.to_dict())), level='info')
        variable_cache.store_variable(variable=Variable(name='{}:{}'.format(self.kind, self.metadata['name']), initial_value='Some Result Worth Saving'))
        variable_cache.store_variable(variable=Variable(name='{}:{}-val'.format(self.kind, self.metadata['name']), initial_value=None), overwrite_existing=True)
        variable_cache.store_variable(variable=Variable(name='{}:{}-applied'.format(self.kind, self.metadata['name']), initial_value=False), overwrite_existing=True)
        variable_cache.store_variable(variable=Variable(name='{}:{}-deleted'.format(self.kind, self.metadata['name']), initial_value=True), overwrite_existing=True)
        return  
    

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

    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders())->bool:
        return True # We are always different

    def apply_manifest(self, manifest_lookup_function: object=manifest_lookup_that_always_returns_MyManifest1, variable_cache: VariableCache=VariableCache(), target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders()):
        if 'parent' in self.spec:
            m1 = manifest_lookup_function(name=self.spec['parent'])
            m1.apply_manifest(variable_cache=variable_cache)
        variable_cache.store_variable(variable=Variable(name='{}:{}'.format(self.kind, self.metadata['name']), initial_value='Another value worth storing'))
        variable_cache.store_variable(variable=Variable(name='{}:{}-val'.format(self.kind, self.metadata['name']), initial_value=self.spec['val']), overwrite_existing=True)
        variable_cache.store_variable(variable=Variable(name='{}:{}-applied'.format(self.kind, self.metadata['name']), initial_value=True), overwrite_existing=True)
        variable_cache.store_variable(variable=Variable(name='{}:{}-deleted'.format(self.kind, self.metadata['name']), initial_value=False), overwrite_existing=True)
        return  # Assume some implementation
    
    def delete_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders()):
        variable_cache.store_variable(variable=Variable(name='{}:{}'.format(self.kind, self.metadata['name']), initial_value='Some Result Worth Saving'))
        variable_cache.store_variable(variable=Variable(name='{}:{}-val'.format(self.kind, self.metadata['name']), initial_value=None), overwrite_existing=True)
        variable_cache.store_variable(variable=Variable(name='{}:{}-applied'.format(self.kind, self.metadata['name']), initial_value=False), overwrite_existing=True)
        variable_cache.store_variable(variable=Variable(name='{}:{}-deleted'.format(self.kind, self.metadata['name']), initial_value=True), overwrite_existing=True)
        return


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

    def setUp(self):
        print('-'*80)

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

    def setUp(self):
        print('-'*80)

    def test_init_with_defaults(self):
        m2 = MyManifest2(post_parsing_method=my_post_parsing_method)
        m2.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=my_manifest_2_data)['part_1'])
        vc = VariableCache()
        m2.apply_manifest(manifest_lookup_function=manifest_lookup_that_always_returns_MyManifest1, variable_cache=vc)
        self.assertEqual(len(vc.values), 8)

        print('='*80)
        print('# TestMyManifest2.test_init_with_defaults Variables')
        print(str(vc))
        print('='*80)

        self.assertTrue('MyManifest1:test1' in vc.values)
        self.assertTrue('MyManifest2:test2' in vc.values)
        self.assertEqual(vc.get_value(variable_name='MyManifest1:test1'), 'Some Result Worth Saving')
        self.assertEqual(vc.get_value(variable_name='MyManifest2:test2'), 'Another value worth storing')


class TestManifestBaseVariableAndValueSubstitution(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        self.vc = VariableCache()
        self.vc.store_variable(variable=Variable(name='some:name-123', initial_value='val1'))
        self.vc.store_variable(variable=Variable(name='some-other:name:456', initial_value='val2', mask_in_logs=True))
        self.vps = ValuePlaceHolders(logger=get_logger())
        self.vps.add_environment_value(placeholder_name='test3', environment_name='default', value='val3')
        self.vps.add_environment_value(placeholder_name='test4', environment_name='default', value='val4')

    @mock.patch.dict(os.environ, {"DEBUG": "1"})   
    def test_basic_substitution(self):
        manifest_data =  """---
kind: MyManifest1
version: v0.1
metadata:
  name: test1
spec:
    val: 1
    more:
    - 'First Value'
    - '{}{} .Variables.some:name-123 {}{}'
    - '{}{} .Variables.some-other:name:456 {}{}'
    - '{}{} .Values.test3 {}{}'
    - '{}{} .Values.test4 {}{}'
    - 'Last Value'
""".format(
            '{','{','}','}',
            '{','{','}','}',
            '{','{','}','}',
            '{','{','}','}'
        )
        m = MyManifest1(post_parsing_method=my_post_parsing_method)
        m.metadata['environments'] = ['default']
        m.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_data)['part_1'])
        m.process_dependencies(
            action='apply',
            process_dependency_if_already_applied=False,
            process_dependency_if_not_already_applied=False,
            manifest_lookup_function=manifest_lookup_that_always_returns_MyManifest1,
            variable_cache=self.vc,
            process_self_post_dependency_processing=True,
            value_placeholders=self.vps,
            target_environment='default'
        )

        spec = copy.deepcopy(m.spec)
        self.assertIsNotNone(spec)
        self.assertIsInstance(spec, dict)
        self.assertTrue('more' in spec)
        more = copy.deepcopy(spec['more'])
        self.assertIsNotNone(more)
        self.assertIsInstance(more, list)
        expected_values = (
            'First Value',
            'val1',
            'val2',
            'val3',
            'val4',
            'Last Value',
        )
        print()
        print()
        print('spec={}'.format(json.dumps(spec)))
        print()
        print()
        for expected_value in expected_values:
            self.assertTrue(expected_value in more, 'Expected "{}" to be in list'.format(expected_value))


class MyServiceX(ManifestBase): # pragma: no cover

    def __init__(self, logger=get_logger(), post_parsing_method: object = my_post_parsing_method, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def _var_name(self, target_environment: str='default'):
        return '{}:{}:{}'.format(
            self.__class__.__name__,
            self.metadata['name'],
            target_environment
        )

    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders())->bool:
        return True
    
    def apply_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders()):
        variable_cache.store_variable(
            variable=Variable(
                name='{}:VAL_X'.format(self._var_name(target_environment=target_environment)), 
                initial_value='Hello'
            )
        )


class MyServiceY(ManifestBase): # pragma: no cover

    def __init__(self, logger=get_logger(), post_parsing_method: object = my_post_parsing_method, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def _var_name(self, target_environment: str='default'):
        return '{}:{}:{}'.format(
            self.__class__.__name__,
            self.metadata['name'],
            target_environment
        )
    
    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders())->bool:
        return True

    def apply_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders()):
        variable_cache.store_variable(
            variable=Variable(
                name='{}:VAL_Y'.format(self._var_name(target_environment=target_environment)), 
                initial_value='{}'.format(self.spec['greetingText'])
            )
        )


class TestManifestBaseVariableSubstitutionDemo(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        self.manifest_data_service_x = """---
kind: MyServiceX
version: v1
metadata:
  name: service-x
spec:
  greeting: 'Hello'
        """
        self.manifest_data_service_y = """---
kind: MyServiceY
version: v1
metadata:
  name: service-y
  dependencies:
    apply: 
    - service-x
spec:
  greetingText: 'I say: {}{} .Variables.MyServiceX:service-x:default:VAL_X {}{} world!'
        """.format(
            '{','{','}','}'
        )
        self.vc = VariableCache()
        self.vps = ValuePlaceHolders(logger=get_logger())

    @mock.patch.dict(os.environ, {"DEBUG": "1"})
    def test_demo_variable_substitution(self):
        service_x_impl = MyServiceX(post_parsing_method=my_post_parsing_method)
        service_x_impl.metadata['environments'] = ['default']
        
        service_y_impl = MyServiceY(post_parsing_method=my_post_parsing_method)
        service_y_impl.metadata['environments'] = ['default']

        mm = ManifestManager(variable_cache=self.vc, logger=get_logger())
        mm.versioned_class_register.add_class(clazz=service_x_impl)
        mm.versioned_class_register.add_class(clazz=service_y_impl)

        parsed_data = parse_raw_yaml_data(yaml_data=self.manifest_data_service_x)
        for part_id, data_as_dict in parsed_data.items():
            if 'version' in data_as_dict and 'kind' in data_as_dict and 'metadata' in data_as_dict:
                mm.parse_manifest(manifest_data=data_as_dict)
        parsed_data = parse_raw_yaml_data(yaml_data=self.manifest_data_service_y)
        for part_id, data_as_dict in parsed_data.items():
            if 'version' in data_as_dict and 'kind' in data_as_dict and 'metadata' in data_as_dict:
                mm.parse_manifest(manifest_data=data_as_dict)

        # This should automatically first process the dependant manifest
        mm.apply_manifest(name='service-y')

        result = self.vc.get_value(variable_name='MyServiceY:service-y:default:VAL_Y')
        self.assertEqual(result, 'I say: Hello world!')


class TestManifestManager(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('*'*80)
        if os.path.exists('/tmp/test_manifest_classes'):
            if os.path.isdir(s='/tmp/test_manifest_classes'):
                shutil.rmtree(path='/tmp/test_manifest_classes', ignore_errors=True)
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
        self.assertEqual(len(mm.versioned_class_register.classes), 6)

        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=my_manifest_1_data)['part_1'])
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=my_manifest_2_data)['part_1'])
        self.assertEqual(len(mm.manifest_instances), 2)
        for key in tuple(mm.manifest_instances.keys()):
            self.assertTrue(key.startswith('test'))

        mm.apply_manifest(name='test2')
        self.assertEqual(len(vc.values), 8)
        self.assertTrue('MyManifest1:test1' in vc.values)
        self.assertTrue('MyManifest2:test2' in vc.values)
        self.assertEqual(vc.values['MyManifest1:test1'].value, 'Result from MyManifest1 "v0.1" applying manifest named "test1" with manifest version "v0.1"')
        self.assertEqual(vc.values['MyManifest2:test2'].value, 'Result from MyManifest2 "v0.2" applying manifest named "test2" with manifest version "v0.2"')
        for k,v in vc.values.items():
            print('{}={}'.format(k,v.value))

        # Test exceptions
        with self.assertRaises(Exception) as context:
            mm.get_manifest_class_by_kind(kind='NotRegisteredKind')
        self.assertTrue('Version is required' in str(context.exception))

        with self.assertRaises(Exception) as context:
            mm.get_manifest_instance_by_name(name='does-not-exist')
        self.assertTrue('No manifest instance for "does-not-exist" found' in str(context.exception))

    def test_multiple_versions_of_manifest(self):
        ###
        ### Manifest Setup
        ###

        manifest_1_v01_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-1
spec:
    val: 1
    more:
    - one
    - two
    - three
"""

        manifest_1_v02_data =  """---
    kind: MyManifest1
    version: v0.2
    metadata:
        name: test1-2
    spec:
        val: 2
        more:
        - four
        - five
        - six
"""

        manifest_1_v03_data =  """---
    kind: MyManifest1
    version: v0.3
    metadata:
        name: test1-3
    spec:
        val: 3
        more:
        - seven
"""

        manifest_2_v01_data=  """---
kind: MyManifest2
version: v0.1
metadata:
    name: test2-1
spec:
    val: AAA
    parent: test1-2
"""

        manifest_2_v02_data=  """---
kind: MyManifest2
version: v0.2
metadata:
    name: test2-2
spec:
    val: BBB
    parent: test1-2
"""

        manifest_2_v03_data=  """---
kind: MyManifest2
version: v0.3
metadata:
    name: test2-3
spec:
    val: CCC
    parent: test1-2
"""

        ###
        ### Init VariableCache and ManifestManager
        ###
        vc = VariableCache()
        mm = ManifestManager(variable_cache=vc)

        ###
        ### Consume classes that extend ManifestBase and register with ManifestManager
        ###
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test1')
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test2')
        self.assertEqual(len(mm.versioned_class_register.classes), 6)

        ###
        ### Consume Manifests and link with class implementations registered in ManifestManager
        ###
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v01_data)['part_1'])
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v02_data)['part_1'])
        # mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v03_data)['part_1']) # Deliberately leave this one out - pretend it is still in concept phase or something...
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_2_v03_data)['part_1'])
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_2_v02_data)['part_1'])
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_2_v01_data)['part_1'])
        
        

        self.assertEqual(len(mm.versioned_class_register.classes), 6)
        self.assertEqual(len(mm.manifest_instances), 5)         # One less, if "manifest_1_v03_data" is not parsed (commented out above)

        ###
        ### Mimic the main() function apply all call
        ###
        for name in tuple(mm.manifest_instances.keys()):
            print('Applying manifest named "{}"'.format(name))
            mm.apply_manifest(name=name)
        for name in tuple(vc.values.keys()):
            print('RESULT: {}={}'.format(name, vc.get_value(variable_name=name)))

        var_names = (
            'MyManifest1:test1-1',
            'MyManifest1:test1-2',
            'MyManifest2:test2-1',
            'MyManifest2:test2-2',
            'MyManifest2:test2-3'
        )
        for v_name in var_names:
            self.assertIsNotNone(vc.get_value(variable_name=v_name), 'Unexpected None for variable named "{}"'.format(v_name))
        

        ###
        ### Test mm.get_manifest_class_by_kind() call for kind with no version - ensure we get the latest version
        ###
        latest_instance_of_manifest2 = mm.get_manifest_class_by_kind(kind='MyManifest2', version='v0.3')
        self.assertIsNotNone(latest_instance_of_manifest2)
        self.assertIsInstance(latest_instance_of_manifest2, ManifestBase)
        self.assertEqual(latest_instance_of_manifest2.kind, 'MyManifest2')
        self.assertEqual(latest_instance_of_manifest2.version, 'v0.3')

        ###
        ### Mimic the main() function delete all call
        ###
        for ref in tuple(mm.manifest_instances.keys()):
            name, version, checksum = ref.split(':')
            print('Deleting manifest named "{}" version "{}'.format(name, version))
            # mm.delete_manifest(name=name, version=version)
            mm.delete_manifest(name=name)
        for v_name in var_names:
            with self.assertRaises(Exception) as context:
                vc.get_value(variable_name=v_name)
            self.assertTrue('Expired' in str(context.exception), 'Expected variable named "{}" to have expired!'.format(v_name))

    def test_multiple_skip_apply_all_and_delete_all_scenarios(self):
        ###
        ### Manifest Setup
        ###

        manifest_1_v01_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-1
    skipApplyAll: true
    skipDeleteAll: true
spec:
    val: 1
    more:
    - one
    - two
    - three
"""

        manifest_2_v01_data=  """---
kind: MyManifest2
version: v0.1
metadata:
    name: test2-1
spec:
    val: AAA
    parent: test1-1
"""


        ###
        ### Init VariableCache and ManifestManager
        ###
        vc = VariableCache()
        mm = ManifestManager(variable_cache=vc)

        ###
        ### Consume classes that extend ManifestBase and register with ManifestManager
        ###
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test1')
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test2')
        self.assertEqual(len(mm.versioned_class_register.classes), 6)

        ###
        ### Consume Manifests and link with class implementations registered in ManifestManager
        ###
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v01_data)['part_1'])
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_2_v01_data)['part_1'])

        self.assertEqual(len(mm.versioned_class_register.classes), 6)
        self.assertEqual(len(mm.manifest_instances), 2)

        ###
        ### Mimic the main() function apply all call
        ###
        for name in tuple(mm.manifest_instances.keys()):
            print('Applying manifest named "{}"'.format(name))
            mm.apply_manifest(name=name)
        result1 = vc.get_value(variable_name='MyManifest1:test1-1')    # Ensure that processing manifest 2, that manifest 1 was executed
        self.assertIsNotNone(result1)
        for name in tuple(vc.values.keys()):
            print('RESULT: {}={}'.format(name, vc.get_value(variable_name=name))) 

        ###
        ### Mimic the main() function delete all call
        ###
        for ref in tuple(mm.manifest_instances.keys()):
            name, version, checksum = ref.split(':')
            print('Deleting manifest named "{}" version "{}'.format(name, version))
            # mm.delete_manifest(name=name, version=version)
            mm.delete_manifest(name=name)
        for v_name in ('MyManifest2:test2-1',):
            with self.assertRaises(Exception) as context:
                vc.get_value(variable_name=v_name)
            self.assertTrue('Expired' in str(context.exception), 'Expected variable named "{}" to have expired!'.format(v_name))
        result2 = vc.get_value(variable_name='MyManifest1:test1-1')    # Implementation dictates that this variables must still be available
        self.assertIsNotNone(result2)

    def test_dependency_scenarios(self):
        ###
        ### Manifest Setup
        ###

        manifest_1_v01_a_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-1
    skipApplyAll: true
    skipDeleteAll: true
spec:
    val: 1
"""

        manifest_1_v01_b_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-2
    skipApplyAll: true
    skipDeleteAll: true
spec:
    val: 0
"""

        manifest_2_v01_data=  """---
kind: MyManifest2
version: v0.1
metadata:
    name: test2-1
    dependencies:
        apply:
        - test1-1
        delete:
        - test1-2
spec:
    val: AAA
"""


        ###
        ### Init VariableCache and ManifestManager
        ###
        vc = VariableCache()
        mm = ManifestManager(variable_cache=vc)

        ###
        ### Consume classes that extend ManifestBase and register with ManifestManager
        ###
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test1')
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test2')
        self.assertEqual(len(mm.versioned_class_register.classes), 6)

        ###
        ### Consume Manifests and link with class implementations registered in ManifestManager
        ###
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v01_a_data)['part_1'])
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v01_b_data)['part_1'])
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_2_v01_data)['part_1'])

        self.assertEqual(len(mm.versioned_class_register.classes), 6)
        self.assertEqual(len(mm.manifest_instances), 3)

        ###
        ### Mimic the main() function apply all call
        ###
        for name in tuple(mm.manifest_instances.keys()):
            print('Applying manifest named "{}"'.format(name))
            mm.apply_manifest(name=name)
        result1 = vc.get_value(variable_name='MyManifest1:test1-1')    # Ensure that processing manifest 2, that manifest 1 was executed
        self.assertIsNotNone(result1)
        for name in tuple(vc.values.keys()):
            print('RESULT: {}={}'.format(name, vc.get_value(variable_name=name))) 

        ###
        ### Mimic the main() function delete all call
        ###
        for ref in tuple(mm.manifest_instances.keys()):
            name, version, checksum = ref.split(':')
            print('Deleting manifest named "{}" version "{}'.format(name, version))
            # mm.delete_manifest(name=name, version=version)
            mm.delete_manifest(name=name)
        for v_name in ('MyManifest2:test2-1',):
            with self.assertRaises(Exception) as context:
                vc.get_value(variable_name=v_name)
            self.assertTrue('Expired' in str(context.exception), 'Expected variable named "{}" to have expired!'.format(v_name))
        result2 = vc.get_value(variable_name='MyManifest1:test1-1')    # Implementation dictates that this variables must still be available
        self.assertIsNotNone(result2)

    def test_skip_dependency_scenarios(self):
        ###
        ### Manifest Setup
        ###

        manifest_1_v01_a_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-1
    skipApplyAll: true
    skipDeleteAll: true
spec:
    val: 1
"""

        manifest_1_v01_b_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-2
    skipApplyAll: true
    skipDeleteAll: true
spec:
    val: 0
"""

        manifest_2_v01_data=  """---
kind: MyManifest2
version: v0.1
metadata:
    name: test2-1
    dependencies:
        apply:
        - test1-1
        delete:
        - test1-2
spec:
    val: AAA
"""


        ###
        ### Init VariableCache and ManifestManager
        ###
        vc = VariableCache()
        mm = ManifestManager(variable_cache=vc)

        ###
        ### Consume classes that extend ManifestBase and register with ManifestManager
        ###
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test1')
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test2')
        self.assertEqual(len(mm.versioned_class_register.classes), 6)

        ###
        ### Consume Manifests and link with class implementations registered in ManifestManager
        ###
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v01_a_data)['part_1'])
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v01_b_data)['part_1'])
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_2_v01_data)['part_1'])

        self.assertEqual(len(mm.versioned_class_register.classes), 6)
        self.assertEqual(len(mm.manifest_instances), 3)

        ###
        ### Mimic the main() function apply all call
        ###
        for name in tuple(mm.manifest_instances.keys()):
            print('Applying manifest named "{}"'.format(name))
            mm.apply_manifest(name=name, skip_dependency_processing=True)
        result1 = vc.get_value(variable_name='MyManifest1:test1-1', raise_exception_on_not_found=False, default_value_if_not_found=None)    # Ensure that processing manifest 2, that manifest 1 was NOT executed
        self.assertIsNone(result1)
        for name in tuple(vc.values.keys()):
            print('RESULT: {}={}'.format(name, vc.get_value(variable_name=name))) 

        ###
        ### Mimic the main() function delete all call
        ###
        for ref in tuple(mm.manifest_instances.keys()):
            name, version, checksum = ref.split(':')
            print('Deleting manifest named "{}" version "{}'.format(name, version))
            # mm.delete_manifest(name=name, version=version)
            mm.delete_manifest(name=name, skip_dependency_processing=True)
        for v_name in ('MyManifest2:test2-1',):
            with self.assertRaises(Exception) as context:
                vc.get_value(variable_name=v_name)
            self.assertTrue('Expired' in str(context.exception), 'Expected variable named "{}" to have expired!'.format(v_name))
        result2 = vc.get_value(variable_name='MyManifest1:test1-1', raise_exception_on_not_found=False, default_value_if_not_found=None)    # Implementation dictates that this variables must still not be available
        self.assertIsNone(result2)

    def test_direct_circular_reference_in_apply_raise_exception(self):
        ###
        ### Manifest Setup
        ###

        manifest_1_v01_a_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-1
    dependencies:
        apply:
            - test1-2
spec:
    val: 1
"""

        manifest_1_v01_b_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-2
    dependencies:
        apply:
            - test1-1
spec:
    val: 1
"""

        ###
        ### Init VariableCache and ManifestManager
        ###
        vc = VariableCache()
        mm = ManifestManager(variable_cache=vc)

        ###
        ### Consume classes that extend ManifestBase and register with ManifestManager
        ###
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test1')
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test2')
        self.assertEqual(len(mm.versioned_class_register.classes), 6)

        ###
        ### Consume Manifests and link with class implementations registered in ManifestManager
        ###
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v01_a_data)['part_1'])
        with self.assertRaises(Exception) as context:
            mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v01_b_data)['part_1'])
        self.assertTrue('Direct dependency violation detected in class' in str(context.exception))

    def test_direct_circular_reference_in_delete_raise_exception(self):
        ###
        ### Manifest Setup
        ###

        manifest_1_v01_a_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-1
    dependencies:
        delete:
            - test1-2
spec:
    val: 1
"""

        manifest_1_v01_b_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-2
    dependencies:
        delete:
            - test1-1
spec:
    val: 1
"""

        ###
        ### Init VariableCache and ManifestManager
        ###
        vc = VariableCache()
        mm = ManifestManager(variable_cache=vc)

        ###
        ### Consume classes that extend ManifestBase and register with ManifestManager
        ###
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test1')
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test2')
        self.assertEqual(len(mm.versioned_class_register.classes), 6)

        ###
        ### Consume Manifests and link with class implementations registered in ManifestManager
        ###
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v01_a_data)['part_1'])
        with self.assertRaises(Exception) as context:
            mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v01_b_data)['part_1'])
        self.assertTrue('Direct dependency violation detected in class' in str(context.exception))

    @mock.patch.dict(os.environ, {"DEBUG": "1"})
    def test_indirect_circular_reference_in_apply_raise_exception(self):
        ###
        ### Manifest Setup
        ###

        manifest_1_v01_a_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-1
    dependencies:
        apply:
            - test1-3
        delete:
            - test1-3
spec:
    val: 1
"""

        manifest_1_v01_b_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-2
    dependencies:
        apply:
            - test1-1
        delete:
            - test1-1
spec:
    val: 1
"""

        manifest_1_v01_c_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-3
    dependencies:
        apply:
            - test1-2
        delete:
            - test1-2
spec:
    val: 1
"""

        ###
        ### Init VariableCache and ManifestManager
        ###
        vc = VariableCache()
        mm = ManifestManager(variable_cache=vc, max_calls_to_manifest=2)    # Force an exception the moment any manifest is implemented more than once

        ###
        ### Consume classes that extend ManifestBase and register with ManifestManager
        ###
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test1')
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test2')
        self.assertEqual(len(mm.versioned_class_register.classes), 6)

        ###
        ### Consume Manifests and link with class implementations registered in ManifestManager
        ###
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v01_a_data)['part_1'])
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v01_b_data)['part_1'])
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v01_c_data)['part_1'])

        ###
        ### Mimic the main() function apply all call
        ###
        # for name in tuple(mm.manifest_instances.keys()):
        #     print('Applying manifest named "{}"'.format(name))
        #     mm.apply_manifest(name=name, skip_dependency_processing=False)
        with self.assertRaises(Exception) as context:
            for name in tuple(mm.manifest_instances.keys()):
                print('Applying manifest named "{}"'.format(name))
                mm.apply_manifest(name=name)
        self.assertTrue('Possible recursion detected' in str(context.exception))
        mm.executions_per_manifest_instance = dict()
        
        ###
        ### Mimic the main() function delete all call
        ###
        with self.assertRaises(Exception) as context:
            for name in tuple(mm.manifest_instances.keys()):
                print('Deleting manifest named "{}"'.format(name))
                mm.delete_manifest(name=name, skip_dependency_processing=False)
        self.assertTrue('Possible recursion detected' in str(context.exception))

    def test_with_skip_dependency_processing_indirect_circular_reference_in_apply_not_raise_exception(self):
        ###
        ### Manifest Setup
        ###

        manifest_1_v01_a_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-1
    dependencies:
        apply:
            - test1-3
        delete:
            - test1-3
spec:
    val: 1
"""

        manifest_1_v01_b_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-2
    dependencies:
        apply:
            - test1-1
        delete:
            - test1-1
spec:
    val: 1
"""

        manifest_1_v01_c_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-3
    dependencies:
        apply:
            - test1-2
        delete:
            - test1-2
spec:
    val: 1
"""

        ###
        ### Init VariableCache and ManifestManager
        ###
        vc = VariableCache()
        mm = ManifestManager(variable_cache=vc, max_calls_to_manifest=1)    # Force an exception the moment any manifest is implemented more than once

        ###
        ### Consume classes that extend ManifestBase and register with ManifestManager
        ###
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test1')
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test2')
        self.assertEqual(len(mm.versioned_class_register.classes), 6)

        ###
        ### Consume Manifests and link with class implementations registered in ManifestManager
        ###
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v01_a_data)['part_1'])
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v01_b_data)['part_1'])
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v01_c_data)['part_1'])

        ###
        ### Mimic the main() function apply all call
        ###
        for name in tuple(mm.manifest_instances.keys()):
            print('Applying manifest named "{}"'.format(name))
            mm.apply_manifest(name=name, skip_dependency_processing=True)
        mm.executions_per_manifest_instance = dict()
        
        ###
        ### Mimic the main() function delete all call
        ###
        for name in tuple(mm.manifest_instances.keys()):
            print('Deleting manifest named "{}"'.format(name))
            mm.delete_manifest(name=name, skip_dependency_processing=True)

    @mock.patch.dict(os.environ, {"DEBUG": "1"})        
    def test_manifests_with_multiple_environments_and_only_one_environment_selected(self):
        ###
        ### Manifest Setup
        ###

        manifest_1_v01_a_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-1
    environments:
    - env1
    - env2
    - env3
spec:
    val: 1
"""

        # THIS ONE SHOULD NOT BE APPLIED... MISSING env3
        manifest_1_v01_b_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-2
    environments:
    - env1
    - env2
spec:
    val: 1
"""

        manifest_1_v01_c_data =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1-3
    environments:
    - env2
    - env3
spec:
    val: 1
"""

        ###
        ### Init VariableCache and ManifestManager
        ###
        vc = VariableCache()
        mm = ManifestManager(variable_cache=vc, max_calls_to_manifest=1, environments=['env3',])

        ###
        ### Consume classes that extend ManifestBase and register with ManifestManager
        ###
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test1')
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test2')
        self.assertEqual(len(mm.versioned_class_register.classes), 6)

        ###
        ### Consume Manifests and link with class implementations registered in ManifestManager
        ###
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v01_a_data)['part_1'])
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v01_b_data)['part_1'])
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=manifest_1_v01_c_data)['part_1'])

        ###
        ### Mimic the main() function apply all call
        ###
        print()
        print('#################### APPLY ####################')
        for target_environment in ('env3',):
            print('   >>> Target Environment: {}'.format(target_environment))
            for name in tuple(mm.manifest_instances.keys()):
                print('---------- Applying manifest named "{}"'.format(name))
                mm.apply_manifest(name=name, skip_dependency_processing=True, target_environment=target_environment)
        mm.executions_per_manifest_instance = dict()
        
        ###
        ### Mimic the main() function delete all call
        ###
        print()
        print('#################### DELETE ####################')
        for target_environment in ('env3',):
            print('   >>> Target Environment: {}'.format(target_environment))
            for name in tuple(mm.manifest_instances.keys()):
                print('---------- Deleting manifest named "{}"'.format(name))
                mm.delete_manifest(name=name, skip_dependency_processing=True, target_environment=target_environment)

        vc_dict = vc.to_dict()

        print()
        print('#################### RESULTS ####################')
        print('   vc_dict={}'.format(json.dumps(vc_dict)))

        ### Validate Target Environments - test1-2 should not be applied or deleted
        manifest_names = ('test1-1', 'test1-2', 'test1-3', )
        target_environments = {
            'applied': ('test1-1', 'test1-3', ),
            'deleted': ('test1-1', 'test1-3', ),
        }
        for action in tuple(target_environments.keys()):
            for manifest_name in manifest_names:
                variable_name = 'MyManifest1:{}-{}'.format(manifest_name, action)
                print('> Testing variable "{}" for action "{}"'.format(variable_name, action))
                if manifest_name not in target_environments[action]:
                    print('>   Manifest "{}" NOT targeted for action "{}"'.format(manifest_name, action))
                    self.assertEqual(manifest_name, 'test1-2', 'Expected manifest named test1-2')
                else:
                    print('>   Manifest "{}" targeted for action "{}"'.format(manifest_name, action))
                    variable_value = vc.get_value(variable_name=variable_name, value_if_expired=None, default_value_if_not_found=None, raise_exception_on_expired=False, raise_exception_on_not_found=False)
                    self.assertIsNotNone(variable_value, 'Not expecting a None for variable name "{}" for action "{}"'.format(variable_name, action))
                    self.assertTrue(variable_value)


class TestVersionedClassRegister(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)

    def test_init_with_defaults(self):
        registry = VersionedClassRegister()
        self.assertIsNotNone(registry)
        self.assertIsInstance(registry, VersionedClassRegister)
        c1 = ManifestBase(version='v2', supported_versions=['v1', 'v2',])
        c2 = ManifestBase(version='v3', supported_versions=['v1', 'v2', 'v3',])
        c3 = ManifestBase(version='v4', supported_versions=['v4',])
        c1.kind = 'Test'
        c2.kind = 'Test'
        c3.kind = 'Test'
        registry.add_class(clazz=c1)
        registry.add_class(clazz=c2)
        registry.add_class(clazz=c3)
        self.assertEqual(len(registry.classes), 3)

        v2 = registry.get_version_of_class(kind='Test', version='v2')
        self.assertEqual(c1, v2)
        self.assertNotEqual(c2, v2)
        self.assertNotEqual(c3, v2)

        v3 = registry.get_version_of_class(kind='Test', version='v3')
        self.assertEqual(c2, v3)
        self.assertNotEqual(c1, v3)
        self.assertNotEqual(c3, v3)

        v4 = registry.get_version_of_class(kind='Test', version='v4')
        self.assertEqual(c3, v4)
        self.assertNotEqual(c1, v4)
        self.assertNotEqual(c2, v4)

        # Scenario: Version one class is no longer ingested, but several newer classes still support processing
        # manifests of version 1. Return the latest implementation of a class supporting version 1 processing.
        v1 = registry.get_version_of_class(kind='Test', version='v1')
        self.assertEqual(c2, v1)
        self.assertNotEqual(c1, v1)
        self.assertNotEqual(c3, v1)
        self.assertEqual(c2.version, 'v3')


class TestValuePlaceholder(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)

    def test_init_with_defaults(self):
        vp = ValuePlaceholder(placeholder_name='test1')
        self.assertIsNotNone(vp)
        self.assertIsInstance(vp, ValuePlaceholder)
        self.assertEqual(vp.placeholder_name, 'test1')

    def test_two_environments(self):
        vp = ValuePlaceholder(placeholder_name='test1')
        vp.add_environment_value(environment_name='e1', value='v1')
        vp.add_environment_value(environment_name='e2', value='v2')
        self.assertIsNotNone(vp.per_environment_values)
        self.assertTrue('e1' in vp.per_environment_values)
        self.assertTrue('e2' in vp.per_environment_values)
        self.assertEqual(vp.per_environment_values['e1'], 'v1')
        self.assertEqual(vp.per_environment_values['e2'], 'v2')

        print('vp={}'.format(json.dumps(vp.to_dict())))

    def test_get_value(self):
        vp = ValuePlaceholder(placeholder_name='test1')
        vp.add_environment_value(environment_name='e1', value='v1')
        vp.add_environment_value(environment_name='e2', value='v2')
        v1 = vp.get_environment_value(environment_name='e1')
        v2 = vp.get_environment_value(environment_name='e2')
        self.assertEqual(v1, 'v1')
        self.assertEqual(v2, 'v2')

    def test_to_dict(self):
        """
            Expecting {"name": "test1", "environments": [{"environmentName": "e1", "value": "v1"}, {"environmentName": "e2", "value": "v2"}]}
        """
        vp = ValuePlaceholder(placeholder_name='test1')
        vp.add_environment_value(environment_name='e1', value='v1')
        vp.add_environment_value(environment_name='e2', value='v2')
        d = vp.to_dict()
        self.assertIsNotNone(d)
        self.assertIsInstance(d, dict)
        self.assertTrue('name' in d)
        self.assertTrue('environments' in d)
        self.assertEqual(d['name'], 'test1')
        self.assertIsInstance(d['environments'], list)
        self.assertEqual(len(d['environments']), 2)
        for envs in d['environments']:
            self.assertTrue('environmentName' in envs)
            self.assertTrue('value' in envs)


class TestValuePlaceHolders(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)

    def test_init_with_defaults(self):
        vps = ValuePlaceHolders(logger=get_logger())
        self.assertIsNotNone(vps)
        self.assertIsInstance(vps, ValuePlaceHolders)

    def test_init_set_two_place_holders_each_with_two_same_environments(self):
        vps = ValuePlaceHolders(logger=get_logger())
        vps.add_environment_value(placeholder_name='test1', environment_name='env1', value='val1')
        vps.add_environment_value(placeholder_name='test1', environment_name='env2', value='val2')
        vps.add_environment_value(placeholder_name='test2', environment_name='env1', value='val3')
        vps.add_environment_value(placeholder_name='test2', environment_name='env2', value='val4')

        d = vps.to_dict()
        self.assertIsNotNone(d)
        self.assertIsInstance(d, dict)
        self.assertTrue(len(d) > 0)
        print('d={}'.format(json.dumps(d)))

        """
            Expecting {"values": [{"name": "test1", "environments": [{"environmentName": "env1", "value": "val1"}, {"environmentName": "env2", "value": "val2"}]}, {"name": "test2", "environments": [{"environmentName": "env1", "value": "val3"}, {"environmentName": "env2", "value": "val4"}]}]}
        """
        self.assertTrue('values' in d)
        self.assertIsInstance(d['values'], list)
        for item in d['values']:
            self.assertIsInstance(item, dict)
            self.assertTrue('name' in item)
            self.assertTrue('environments' in item)
            self.assertIsInstance(item['environments'], list)
            for item_env in item['environments']:
                self.assertTrue('environmentName' in item_env)
                self.assertTrue('value' in item_env)

        v1 = vps.get_value_placeholder(placeholder_name='test1').get_environment_value(environment_name='env1')
        v2 = vps.get_value_placeholder(placeholder_name='test1').get_environment_value(environment_name='env2')
        v3 = vps.get_value_placeholder(placeholder_name='test2').get_environment_value(environment_name='env1')
        v4 = vps.get_value_placeholder(placeholder_name='test2').get_environment_value(environment_name='env2')
        self.assertEqual(v1, 'val1')
        self.assertEqual(v2, 'val2')
        self.assertEqual(v3, 'val3')
        self.assertEqual(v4, 'val4')

    def test_get_default_variable_value_for_missing_environment_value(self):
        vps = ValuePlaceHolders(logger=get_logger())
        vps.add_environment_value(placeholder_name='test1', environment_name='env1', value='val1')
        value = vps.get_value_placeholder(placeholder_name='test1').get_environment_value(environment_name='env2', default_value_when_not_found=123, raise_exception_when_not_found=False)
        self.assertIsInstance(value, int)
        self.assertEqual(value, 123)

    def test_string_parsing_simple_string_in_matches_str_out(self):
        vps = ValuePlaceHolders(logger=get_logger())
        vps.add_environment_value(placeholder_name='test1', environment_name='env1', value='val1')
        vps.add_environment_value(placeholder_name='test1', environment_name='env2', value='val2')
        vps.add_environment_value(placeholder_name='test2', environment_name='env1', value='val3')
        vps.add_environment_value(placeholder_name='test2', environment_name='env2', value='val4')

        final_str = vps.parse_and_replace_placeholders_in_string(
            input_str='abc',
            environment_name='env1'
        )
        self.assertEqual(final_str, 'abc')

    def test_string_parsing_env_string_in_parsed_correctly_01(self):
        vps = ValuePlaceHolders(logger=get_logger())
        vps.add_environment_value(placeholder_name='test1', environment_name='env1', value='val1')
        vps.add_environment_value(placeholder_name='test1', environment_name='env2', value='val2')
        vps.add_environment_value(placeholder_name='test2', environment_name='env1', value='val3')
        vps.add_environment_value(placeholder_name='test2', environment_name='env2', value='val4')

        final_str = vps.parse_and_replace_placeholders_in_string(
            input_str='{}{} .Values.test2 {}{}'.format('{','{','}','}'),
            environment_name='env1'
        )
        self.assertEqual(final_str, 'val3')

    def test_string_parsing_env_string_in_parsed_correctly_02(self):
        vps = ValuePlaceHolders(logger=get_logger())
        vps.add_environment_value(placeholder_name='test1', environment_name='env1', value='val1')
        vps.add_environment_value(placeholder_name='test1', environment_name='env2', value='val2')
        vps.add_environment_value(placeholder_name='test2', environment_name='env1', value='val3')
        vps.add_environment_value(placeholder_name='test2', environment_name='env2', value='val4')

        final_str = vps.parse_and_replace_placeholders_in_string(
            input_str='abc{}{} .Values.test2 {}{}def'.format('{','{','}','}'),
            environment_name='env1'
        )
        self.assertEqual(final_str, 'abcval3def')

    def test_string_parsing_env_string_in_parsed_correctly_03(self):
        vps = ValuePlaceHolders(logger=get_logger())
        vps.add_environment_value(placeholder_name='test1', environment_name='env1', value='val1')
        vps.add_environment_value(placeholder_name='test1', environment_name='env2', value='val2')
        vps.add_environment_value(placeholder_name='test2', environment_name='env1', value='val3')
        vps.add_environment_value(placeholder_name='test2', environment_name='env2', value='val4')

        final_str = vps.parse_and_replace_placeholders_in_string(
            input_str='1: {}{} .Values.test1 {}{} and 2: {}{} .Values.test2 {}{}'.format('{','{','}','}','{','{','}','}'),
            environment_name='env1'
        )
        self.assertEqual(final_str, '1: val1 and 2: val3')


class TestValuePlaceHoldersScenarios(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)
        self.manifest_1_v01_a_data =  """---
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

        # THIS ONE SHOULD NOT BE APPLIED... MISSING env3
        self.manifest_1_v01_b_data =  """---
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

        self.manifest_1_v01_c_data =  """---
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
        
        self.vps = ValuePlaceHolders(logger=get_logger())
        self.vps.add_environment_value(placeholder_name='test1', environment_name='env1', value='val1')
        self.vps.add_environment_value(placeholder_name='test1', environment_name='env2', value='val2')
        self.vps.add_environment_value(placeholder_name='test1', environment_name='env3', value='val3')
        self.vps.add_environment_value(placeholder_name='test2', environment_name='env1', value='val4')
        self.vps.add_environment_value(placeholder_name='test2', environment_name='env2', value='val5')
        self.vps.add_environment_value(placeholder_name='test2', environment_name='env3', value='val6')
        self.vps.add_environment_value(placeholder_name='test3', environment_name='env1', value='val7')
        self.vps.add_environment_value(placeholder_name='test3', environment_name='env2', value='val8')
        self.vps.add_environment_value(placeholder_name='test3', environment_name='env3', value='val9')

        if os.path.exists('/tmp/test_manifest_classes'):
            if os.path.isdir(s='/tmp/test_manifest_classes'):
                shutil.rmtree(path='/tmp/test_manifest_classes', ignore_errors=True)
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

        
        print('PREP COMPLETED')
        print('~'*80)

    def tearDown(self):
        if os.path.exists('/tmp/test_manifest_classes'):
            if os.path.isdir(s='/tmp/test_manifest_classes'):
                shutil.rmtree(path='/tmp/test_manifest_classes', ignore_errors=True)

    # @mock.patch.dict(os.environ, {"DEBUG": "1"})   
    def test_init_with_defaults(self):
        ###
        ### Init VariableCache and ManifestManager
        ###
        vc = VariableCache()
        mm = ManifestManager(variable_cache=vc, max_calls_to_manifest=1, environments=['env3',])
        mm.environment_values = self.vps

        ###
        ### Consume classes that extend ManifestBase and register with ManifestManager
        ###
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test1')
        mm.load_manifest_class_definition_from_file(plugin_file_path='/tmp/test_manifest_classes/test2')
        self.assertEqual(len(mm.versioned_class_register.classes), 6)

        ###
        ### Consume Manifests and link with class implementations registered in ManifestManager
        ###
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=self.manifest_1_v01_a_data)['part_1'])
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=self.manifest_1_v01_b_data)['part_1'])
        mm.parse_manifest(manifest_data=parse_raw_yaml_data(yaml_data=self.manifest_1_v01_c_data)['part_1'])

        ###
        ### Mimic the main() function apply all call
        ###
        print()
        print('#################### APPLY ####################')
        for target_environment in ('env3',):
            print('   >>> Target Environment: {}'.format(target_environment))
            for name in tuple(mm.manifest_instances.keys()):
                print('---------- Applying manifest named "{}"'.format(name))
                mm.apply_manifest(name=name, skip_dependency_processing=True, target_environment=target_environment)
        mm.executions_per_manifest_instance = dict()

        vc_data = vc.to_dict()
        print()
        print()
        print('vc={}'.format(json.dumps(vc_data)))
        print()
        print()

        self.assertEqual(vc_data['MyManifest1:test1-1-val']['value'], 'val3')
        self.assertEqual(vc_data['MyManifest1:test1-3-val']['value'], 'val9')

    def test_remove_newline_from_string_values_if_present(self):
        text = """Hello
 world!"""
        expected = "Hello world!"
        self.assertNotEqual(text, expected)
        vps = ValuePlaceHolders(logger=get_logger())
        vps.add_environment_value(placeholder_name='test', environment_name='default', value=text)
        result = vps.get_value_placeholder(placeholder_name='test', create_in_not_exists=True).get_environment_value(environment_name='default')
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertEqual(result, expected)



class TestDependencyReferences(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)

    def test_direct_dependency_negative_test(self):
        drs = DependencyReferences()

        # The following represent a deep circular reference, but will test negative for a direct dependency reference check
        drs.add_dependency(src='a', dst='b')
        drs.add_dependency(src='b', dst='c')
        drs.add_dependency(src='c', dst='a')

        self.assertFalse(drs.direct_circular_references_detected())

    def test_direct_dependency_positive_test(self):
        drs = DependencyReferences()
        drs.add_dependency(src='a', dst='b')
        drs.add_dependency(src='b', dst='a')
        self.assertTrue(drs.direct_circular_references_detected())



if __name__ == '__main__':
    unittest.main()
