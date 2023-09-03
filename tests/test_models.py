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
import time
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
print('sys.path={}'.format(sys.path))

import unittest


from py_animus.models import *

class TestClassValue(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)

    def test_basic_value(self):
        v = Value(name='test-name', initial_value='test-value')
        self.assertIsNotNone(v)
        self.assertIsInstance(v, Value)
        self.assertTrue(v.name == 'test-name')
        self.assertTrue(v.value == 'test-value')
        v.update_value(new_value='test-value-2')
        self.assertTrue(v.value == 'test-value-2')
        self.assertFalse(v.value == 'test-value')


class TestClassValues(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)
        self.v1 = Value(name='test-name-1', initial_value='test-value-1')
        self.v2 = Value(name='test-name-2', initial_value='test-value-2')
        self.v3 = Value(name='test-name-3', initial_value='test-value-3')

    def test_basic_values(self):
        vs = Values()
        self.assertIsNotNone(vs)
        self.assertIsInstance(vs, Values)
        self.assertIsNotNone(vs.values)
        self.assertIsInstance(vs.values, dict)
        self.assertTrue(len(vs.values) == 0)
        vs.add_value(value=self.v1)
        self.assertIsInstance(vs.values, dict)
        self.assertTrue(len(vs.values) == 1)
        vs.add_value(value=self.v2)
        self.assertIsInstance(vs.values, dict)
        self.assertTrue(len(vs.values) == 2)
        vs.add_value(value=self.v3)
        self.assertIsInstance(vs.values, dict)
        self.assertTrue(len(vs.values) == 3)
        v1 = vs.find_value_by_name('test-name-1')
        self.assertIsNotNone(v1)
        self.assertIsInstance(v1, Value)
        self.assertTrue(v1.name == 'test-name-1')
        self.assertTrue(v1.value == 'test-value-1')
        v2 = vs.find_value_by_name('test-name-2')
        self.assertIsNotNone(v2)
        self.assertIsInstance(v2, Value)
        self.assertTrue(v2.name == 'test-name-2')
        self.assertTrue(v2.value == 'test-value-2')
        v3= vs.find_value_by_name('test-name-3')
        self.assertIsNotNone(v3)
        self.assertIsInstance(v3, Value)
        self.assertTrue(v3.name == 'test-name-3')
        self.assertTrue(v3.value == 'test-value-3')

        vs.remove_value(name='test-name-3')
        self.assertIsInstance(vs.values, dict)
        self.assertTrue(len(vs.values) == 2)
        v1 = vs.find_value_by_name('test-name-1')
        self.assertIsNotNone(v1)
        self.assertIsInstance(v1, Value)
        self.assertTrue(v1.name == 'test-name-1')
        self.assertTrue(v1.value == 'test-value-1')
        v2 = vs.find_value_by_name('test-name-2')
        self.assertIsNotNone(v2)
        self.assertIsInstance(v2, Value)
        self.assertTrue(v2.name == 'test-name-2')
        self.assertTrue(v2.value == 'test-value-2')
        with self.assertRaises(Exception):
            vs.find_value_by_name('test-name-3')


class TestClassScopedValues(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)
        self.v1 = Value(name='test-name-1', initial_value='test-value-1')
        self.v2 = Value(name='test-name-2', initial_value='test-value-2')
        self.v3 = Value(name='test-name-3', initial_value='test-value-3')

    def test_basic_values(self):
        svs = ScopedValues(scope='test-scope')
        self.assertIsNotNone(svs)
        self.assertIsInstance(svs, ScopedValues)
        svs.add_value(value=self.v1)
        svs.add_value(value=self.v2)
        svs.add_value(value=self.v3)

        v1 = svs.find_value_by_name('test-name-1')
        self.assertIsNotNone(v1)
        self.assertIsInstance(v1, Value)
        self.assertTrue(v1.name == 'test-name-1')
        self.assertTrue(v1.value == 'test-value-1')
        v2 = svs.find_value_by_name('test-name-2')
        self.assertIsNotNone(v2)
        self.assertIsInstance(v2, Value)
        self.assertTrue(v2.name == 'test-name-2')
        self.assertTrue(v2.value == 'test-value-2')
        v3= svs.find_value_by_name('test-name-3')
        self.assertIsNotNone(v3)
        self.assertIsInstance(v3, Value)
        self.assertTrue(v3.name == 'test-name-3')
        self.assertTrue(v3.value == 'test-value-3')

        svs.remove_value(name='test-name-3')
        v1 = svs.find_value_by_name('test-name-1')
        self.assertIsNotNone(v1)
        self.assertIsInstance(v1, Value)
        self.assertTrue(v1.name == 'test-name-1')
        self.assertTrue(v1.value == 'test-value-1')
        v2 = svs.find_value_by_name('test-name-2')
        self.assertIsNotNone(v2)
        self.assertIsInstance(v2, Value)
        self.assertTrue(v2.name == 'test-name-2')
        self.assertTrue(v2.value == 'test-value-2')
        with self.assertRaises(Exception):
            svs.find_value_by_name('test-name-3')


class TestClassAllScopedValues(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)
        self.v1 = Value(name='test-name-1', initial_value='test-value-1')   # Scope 1
        self.v2 = Value(name='test-name-2', initial_value='test-value-2')   # Scope 2
        self.v3 = Value(name='test-name-3', initial_value='test-value-3')   # Scope 1, again

    def test_basic_all_scoped_values(self):
        asv = AllScopedValues()
        self.assertIsNotNone(asv)
        self.assertIsInstance(asv, AllScopedValues)

        scope1_values = ScopedValues(scope='scope-1')
        scope1_values.add_value(value=self.v1)
        scope1_values.add_value(value=self.v3)

        scope2_values = ScopedValues(scope='scope-2')
        scope2_values.add_value(value=self.v2)
        
        asv.add_scoped_values(scoped_values=scope1_values)
        asv.add_scoped_values(scoped_values=scope2_values)

        result1 = asv.find_scoped_values(scope='scope-1')
        v1 = result1.find_value_by_name('test-name-1')
        self.assertIsNotNone(v1)
        self.assertIsInstance(v1, Value)
        self.assertTrue(v1.name == 'test-name-1')
        self.assertTrue(v1.value == 'test-value-1')
        v3 = result1.find_value_by_name('test-name-3')
        self.assertIsNotNone(v3)
        self.assertIsInstance(v3, Value)
        self.assertTrue(v3.name == 'test-name-3')
        self.assertTrue(v3.value == 'test-value-3')
        with self.assertRaises(Exception):
            result1.find_value_by_name('test-name-2')

        result2 = asv.find_scoped_values(scope='scope-2')
        v2 = result2.find_value_by_name('test-name-2')
        self.assertIsNotNone(v2)
        self.assertIsInstance(v2, Value)
        self.assertTrue(v2.name == 'test-name-2')
        self.assertTrue(v2.value == 'test-value-2')
        with self.assertRaises(Exception):
            result2.find_value_by_name('test-name-1')
        with self.assertRaises(Exception):
            result2.find_value_by_name('test-name-3')
        with self.assertRaises(Exception):
            result2.find_value_by_name('test-name-4')

        v4 = Value(name='test-name-4', initial_value='test-value-4')
        asv.add_value_to_scoped_value(scope='scope-2', value=v4)
        result2b = asv.find_scoped_values(scope='scope-2')
        v2b = result2b.find_value_by_name('test-name-2')
        self.assertIsNotNone(v2b)
        self.assertIsInstance(v2b, Value)
        self.assertTrue(v2b.name == 'test-name-2')
        self.assertTrue(v2b.value == 'test-value-2')
        v4b = result2b.find_value_by_name('test-name-4')
        self.assertIsNotNone(v4b)
        self.assertIsInstance(v4b, Value)
        self.assertTrue(v4b.name == 'test-name-4')
        self.assertTrue(v4b.value == 'test-value-4')
        with self.assertRaises(Exception):
            result2b.find_value_by_name('test-name-1')
        with self.assertRaises(Exception):
            result2b.find_value_by_name('test-name-3')

        with self.assertRaises(Exception):
            asv.find_scoped_values(scope='scope-3')


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

    def test_init_with_default_value_if_not_found(self):
        vc = VariableCache()
        result = vc.get_value(
            variable_name='test',
            value_if_expired='test-value-1',
            default_value_if_not_found='test-value-1',
            raise_exception_on_expired=False,
            raise_exception_on_not_found=False,
            init_with_default_value_if_not_found=True
        )
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertTrue('test-value-1' == result)

        self.assertTrue('test' in vc.values)

        result2 = vc.get_value(
            variable_name='test',
            value_if_expired='test-value-1',
            default_value_if_not_found='test-value-1',
            raise_exception_on_expired=False,
            raise_exception_on_not_found=False,
            init_with_default_value_if_not_found=False
        )
        self.assertIsNotNone(result2)
        self.assertIsInstance(result2, str)
        self.assertTrue('test-value-1' == result2)

    def test_add_dict_item_to_existing_variable(self):
        vc = VariableCache()
        vc.store_variable(
            variable=Variable(
                name='test',
                initial_value=dict()
            )
        )
        vc.add_dict_item_to_existing_variable(
            variable_name='test',
            key='k1',
            value='test-value-1'
        )
        values = vc.get_value(variable_name='test')
        self.assertIsNotNone(values)
        self.assertIsInstance(values, dict)
        self.assertTrue(len(values) == 1)
        self.assertTrue('k1' in values)
        self.assertTrue(values['k1'] == 'test-value-1')

        vc.add_dict_item_to_existing_variable(
            variable_name='test',
            key='k2',
            value='test-value-2'
        )
        values2 = vc.get_value(variable_name='test')
        self.assertIsNotNone(values2)
        self.assertIsInstance(values2, dict)
        self.assertTrue(len(values2) == 2)
        self.assertTrue('k1' in values2)
        self.assertTrue('k2' in values2)
        self.assertTrue(values2['k1'] == 'test-value-1')
        self.assertTrue(values2['k2'] == 'test-value-2')

    def test_update_dict_item_to_existing_dict_variable(self):
        vc = VariableCache()
        vc.store_variable(
            variable=Variable(
                name='test',
                initial_value=dict()
            )
        )
        vc.add_dict_item_to_existing_variable(
            variable_name='test',
            key='k1',
            value='test-value-1'
        )
        values = vc.get_value(variable_name='test')
        self.assertIsNotNone(values)
        self.assertIsInstance(values, dict)
        self.assertTrue(len(values) == 1)
        self.assertTrue('k1' in values)
        self.assertTrue(values['k1'] == 'test-value-1')

        vc.add_dict_item_to_existing_variable(
            variable_name='test',
            key='k1',
            value='test-value-2',
            ignore_if_already_exists=False
        )
        values2 = vc.get_value(variable_name='test')
        self.assertIsNotNone(values2)
        self.assertIsInstance(values2, dict)
        self.assertTrue(len(values2) == 1)
        self.assertTrue('k1' in values2)
        self.assertTrue(values2['k1'] == 'test-value-2')

    def test_add_dict_item_to_existing_variable_not_a_dict_throws_exception(self):
        vc = VariableCache()
        vc.store_variable(
            variable=Variable(
                name='test',
                initial_value=123
            )
        )
        with self.assertRaises(Exception):
            vc.add_dict_item_to_existing_variable(
                variable_name='test',
                key='k1',
                value='test-value-1'
            )

    def test_add_dict_item_to_existing_variable_not_a_dict_returns_empty_dict(self):
        vc = VariableCache()
        vc.store_variable(
            variable=Variable(
                name='test',
                initial_value=123
            )
        )
        values = vc.add_dict_item_to_existing_variable(
            variable_name='test',
            key='k1',
            value='test-value-1',
            raise_exception_if_value_type_is_not_a_dict=False
        )
        self.assertIsNotNone(values)
        self.assertIsInstance(values, dict)
        self.assertTrue(len(values) == 0)

    def test_add_dict_item_to_existing_variable_creates_variable_if_not_already_created(self):
        vc = VariableCache()
        values = vc.add_dict_item_to_existing_variable(
            variable_name='test',
            key='k1',
            value='test-value-1',
            raise_exception_if_value_type_is_not_a_dict=False
        )
        self.assertIsNotNone(values)
        self.assertIsInstance(values, dict)
        self.assertTrue(len(values) == 1)
        self.assertTrue('k1' in values)
        self.assertTrue(values['k1'] == 'test-value-1')

    def test_add_list_item_to_existing_variable(self):
        vc = VariableCache()
        vc.store_variable(
            variable=Variable(
                name='test',
                initial_value=list()
            )
        )
        vc.add_list_item_to_existing_variable(
            variable_name='test',
            value='test-value-1'
        )
        values = vc.get_value(variable_name='test')
        self.assertIsNotNone(values)
        self.assertIsInstance(values, list)
        self.assertTrue(len(values) == 1)
        self.assertTrue('test-value-1' in values)

        vc.add_list_item_to_existing_variable(
            variable_name='test',
            value='test-value-2'
        )
        values2 = vc.get_value(variable_name='test')
        self.assertIsNotNone(values2)
        self.assertIsInstance(values2, list)
        self.assertTrue(len(values2) == 2)
        self.assertTrue('test-value-1' in values2)
        self.assertTrue('test-value-2' in values2)

    def test_add_list_item_to_existing_variable_not_a_list_throws_exception(self):
        vc = VariableCache()
        vc.store_variable(
            variable=Variable(
                name='test',
                initial_value=123
            )
        )
        with self.assertRaises(Exception):
            vc.add_list_item_to_existing_variable(variable_name='test', value='test-value-1')

    def test_add_list_item_to_existing_variable_not_a_list_returns_empty_list(self):
        vc = VariableCache()
        vc.store_variable(
            variable=Variable(
                name='test',
                initial_value=123
            )
        )
        values = vc.add_list_item_to_existing_variable(variable_name='test', value='test-value-1', raise_exception_if_value_type_is_not_a_list=False)
        self.assertIsNotNone(values)
        self.assertIsInstance(values, list)
        self.assertTrue(len(values) == 0)

    def test_add_list_item_to_existing_variable_not_not_yet_exists(self):
        vc = VariableCache()
        values = vc.add_list_item_to_existing_variable(variable_name='test', value='test-value-1')
        self.assertIsNotNone(values)
        self.assertIsInstance(values, list)
        self.assertTrue(len(values) == 1)
        self.assertTrue('test-value-1' in values)


if __name__ == '__main__':
    unittest.main()

