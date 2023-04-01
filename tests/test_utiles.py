"""
    Copyright (c) 2022-2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
print('sys.path={}'.format(sys.path))

import unittest


from py_animus.manifest_management import *
from py_animus.utils import *

running_path = os.getcwd()
print('Current Working Path: {}'.format(running_path))

class TestClassField(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)

    def test_basic_init(self):
        f1 = Field(name='test-name', value='test_value')
        self.assertIsNotNone(f1)
        self.assertIsInstance(f1, Field)
        self.assertEqual(f1.name, 'test-name')
        self.assertEqual(f1.value, 'test_value')

        f1_dict = f1.to_dict()
        self.assertIsNotNone(f1_dict)
        self.assertIsInstance(f1_dict, dict)
        self.assertTrue('test-name' in f1_dict)
        self.assertEqual(f1_dict['test-name'], 'test_value')

    def test_basic_init_none_value(self):
        f1 = Field(name='test-name')
        self.assertIsNotNone(f1)
        self.assertIsInstance(f1, Field)
        self.assertEqual(f1.name, 'test-name')
        self.assertIsNone(f1.value)

        f1_dict = f1.to_dict()
        self.assertIsNotNone(f1_dict)
        self.assertIsInstance(f1_dict, dict)
        self.assertTrue('test-name' in f1_dict)
        self.assertIsNone(f1_dict['test-name'])

    def test_basic_init_nested_field(self):
        f1 = Field(name='test-name1', value='value1')
        f2 = Field(name='test-name2', value=f1)

        f2_dict = f2.to_dict()
        self.assertIsNotNone(f2_dict)
        self.assertIsInstance(f2_dict, dict)
        self.assertTrue('test-name2' in f2_dict)
        self.assertIsNotNone(f2_dict['test-name2'])
        self.assertIsInstance(f2_dict['test-name2'], dict)
        f1_dict = f2_dict['test-name2']
        self.assertIsNotNone(f1_dict)
        self.assertIsInstance(f1_dict, dict)
        self.assertTrue('test-name1' in f1_dict)
        self.assertEqual(f1_dict['test-name1'], 'value1')


class TestFunctionCreateField(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)

    def test_basic_create_nested_field(self):
        f = create_field(dotted_name='a.b', value='value_bbb')
        self.assertIsNotNone(f)
        self.assertIsInstance(f, Field)

        f2_dict = f.to_dict()
        self.assertIsNotNone(f2_dict)
        self.assertIsInstance(f2_dict, dict)
        self.assertTrue('a' in f2_dict)
        self.assertIsNotNone(f2_dict['a'])
        self.assertIsInstance(f2_dict['a'], dict)
        f1_dict = f2_dict['a']
        self.assertIsNotNone(f1_dict)
        self.assertIsInstance(f1_dict, dict)
        self.assertTrue('b' in f1_dict)
        self.assertEqual(f1_dict['b'], 'value_bbb')


class TestFunctionMergeDicts(unittest.TestCase):    # pragma: no cover

    def setUp(self):
        print('-'*80)

    def test_basic(self):
        input_data = '''{
    "kind": "ShellScript",
    "version": "v1",
    "metadata": {
        "name": "shell-script-v1-minimal",
        "skipDeleteAll": true
    },
    "spec": {
        "shellInterpreter": "sh",
        "source.type": "inLine",
        "source.value": "echo \\"Not Yet Implemented\\"",
        "source.test.alt1": "111",
        "source.test.alt2": "222"
    }
}'''

        input_data_converted = json.loads(input_data)
        output_data = dict()
        for t_field_name, t_field_data in input_data_converted.items():
            if isinstance(t_field_data, dict):
                converted_t_field_data = dict()
                for field_name, field_data in t_field_data.items():
                    root_field = create_field(dotted_name=field_name, value=copy.deepcopy(field_data))
                    for k,v in root_field.to_dict().items():
                        if k not in converted_t_field_data:
                            converted_t_field_data[k] = v
                        else:
                            if isinstance(v, dict):
                                converted_t_field_data[k] = merge_dicts(A=converted_t_field_data[k], B=v)
                            else:
                                converted_t_field_data[k] = v
                output_data[t_field_name] = converted_t_field_data
            else:
                output_data[t_field_name] = t_field_data

        for field in ('kind','version','metadata','spec',):
            self.assertTrue(field in output_data, 'Field name "{}" was not found in output_data'.format(field))
            self.assertIsNotNone(output_data[field], 'Field name "{}" was None'.format(field))

        self.assertEqual(output_data['kind'], 'ShellScript')
        self.assertEqual(output_data['version'], 'v1')

        self.assertIsInstance(output_data['metadata'], dict)
        metadata = output_data['metadata']
        for field in ('name','skipDeleteAll',):
            self.assertTrue(field in metadata, 'Field name "{}" was not found in output_data'.format(field))
            self.assertIsNotNone(metadata[field], 'Field name "{}" was None'.format(field))


        """
            spec = {
                "shellInterpreter": "sh",
                "source": {
                    "type": "inLine",
                    "value": "echo \"Not Yet Implemented\"",
                    "test": {
                        "alt1": "111",
                        "alt2": "222"
                    }
                }
            }
        """
        self.assertIsInstance(output_data['spec'], dict)
        spec = output_data['spec']
        for field in ('shellInterpreter','source',):
            self.assertTrue(field in spec, 'Field name "{}" was not found in spec'.format(field))
            self.assertIsNotNone(spec[field], 'Field name "{}" was None'.format(field))
        self.assertEqual(spec['shellInterpreter'], 'sh')

        self.assertIsInstance(spec['source'], dict)
        source = spec['source']
        for field in ('type','value', 'test',):
            self.assertTrue(field in source, 'Field name "{}" was not found in spec'.format(field))
            self.assertIsNotNone(source[field], 'Field name "{}" was None'.format(field))
        self.assertEqual(source['type'], 'inLine')
        self.assertEqual(source['value'], 'echo "Not Yet Implemented"')

        self.assertIsInstance(source['test'], dict)
        test = source['test']
        for field in ('alt1','alt2',):
            self.assertTrue(field in test, 'Field name "{}" was not found in spec'.format(field))
            self.assertIsNotNone(test[field], 'Field name "{}" was None'.format(field))
        self.assertEqual(test['alt1'], '111')
        self.assertEqual(test['alt2'], '222')


if __name__ == '__main__':
    unittest.main()

