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
import copy
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")
print('sys.path={}'.format(sys.path))

import unittest
from unittest import mock
import time


from py_animus.manifest_management import *
from py_animus import get_logger, parse_raw_yaml_data
from py_animus.helpers.work import UnitOfWork, AllWork, ExecutionPlan, UnitOfWorkExceptionHandling

running_path = os.getcwd()
print('Current Working Path: {}'.format(running_path))


class MockLogger:

    def __init__(self):
        self.messages = list()

    def info(self, message):
        self.messages.append('INFO: {}'.format(message))

    def error(self, message):
        self.messages.append('ERROR: {}'.format(message))

    def debug(self, message):
        self.messages.append('DEBUG: {}'.format(message))

    def warning(self, message):
        self.messages.append('WARNING: {}'.format(message))

    def warn(self, message):
        self.warning(message=message)


test_logger = MockLogger()


def my_post_parsing_method(**params):   # pragma: no cover
    print('Working with parameters: {}'.format(params))
    return


class MyManifest1(ManifestBase): # pragma: no cover

    def __init__(self, logger=get_logger(), post_parsing_method: object = my_post_parsing_method, version: str='v0.1', supported_versions: tuple=('v0.1',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders())->bool:
        return True # We are always different

    def apply_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders()):
        self.log(message='[{}] apply_manifest(): MANIFEST: {}'.format(self.metadata['name'], json.dumps(self.to_dict())), level='info')

        variable_cache.store_variable(variable=Variable(name='{}:{}'.format(self.kind, self.metadata['name']), initial_value='Some Result Worth Saving'))
        variable_cache.store_variable(variable=Variable(name='{}:{}-val'.format(self.kind, self.metadata['name']), initial_value=self.spec['val']), overwrite_existing=True)
        variable_cache.store_variable(variable=Variable(name='{}:{}-applied'.format(self.kind, self.metadata['name']), initial_value=True), overwrite_existing=True)
        variable_cache.store_variable(variable=Variable(name='{}:{}-deleted'.format(self.kind, self.metadata['name']), initial_value=False), overwrite_existing=True)
        return  # Assume some implementation
    
    def delete_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders()):
        self.log(message='[{}] delete_manifest(): MANIFEST: {}'.format(self.metadata['name'], json.dumps(self.to_dict())), level='info')

        variable_cache.store_variable(variable=Variable(name='{}:{}'.format(self.kind, self.metadata['name']), initial_value='Some Result Worth Saving'))
        variable_cache.store_variable(variable=Variable(name='{}:{}-val'.format(self.kind, self.metadata['name']), initial_value=None), overwrite_existing=True)
        variable_cache.store_variable(variable=Variable(name='{}:{}-applied'.format(self.kind, self.metadata['name']), initial_value=False), overwrite_existing=True)
        variable_cache.store_variable(variable=Variable(name='{}:{}-deleted'.format(self.kind, self.metadata['name']), initial_value=True), overwrite_existing=True)
        return  
    

class TestUnifiedClasses(unittest.TestCase):    # pragma: no cover

    @mock.patch.dict(os.environ, {"DEBUG": "1"})   
    def setUp(self):
        print('-'*80)

        self.logger = get_logger()

        self.manifest_1 =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test1
    environments:
    - env1
    - env2
    - env3
    skipApplyAll: true
    dependencies:
        delete: 
        - test2
spec:
    val: 'Value 1'
"""

        self.manifest_2 =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test2
    environments:
    - env1
    dependencies:
        apply: 
        - test1
        delete:
        - test3
        - test4
spec:
    val: 'Value 2'
"""

        self.manifest_3 =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test3
    environments:
    - env3
    dependencies:
        apply: 
        - test2
        delete:
        - test4
spec:
    val: 'Value 3'
"""

        self.manifest_4 =  """---
kind: MyManifest1
version: v0.1
metadata:
    name: test4
    environments:
    - env1
    dependencies:
        apply: 
        - test2
        - test3
spec:
    val: 'Value 4'
"""

        self.parsed_manifest_1 = parse_raw_yaml_data(yaml_data=self.manifest_1, logger=self.logger)['part_1']
        self.parsed_manifest_2 = parse_raw_yaml_data(yaml_data=self.manifest_2, logger=self.logger)['part_1']
        self.parsed_manifest_3 = parse_raw_yaml_data(yaml_data=self.manifest_3, logger=self.logger)['part_1']
        self.parsed_manifest_4 = parse_raw_yaml_data(yaml_data=self.manifest_4, logger=self.logger)['part_1']

        self.logger.info('parsed_manifest_1: {}'.format(json.dumps(self.parsed_manifest_1, default=str)))
        self.logger.info('parsed_manifest_2: {}'.format(json.dumps(self.parsed_manifest_2, default=str)))
        self.logger.info('parsed_manifest_3: {}'.format(json.dumps(self.parsed_manifest_3, default=str)))
        self.logger.info('parsed_manifest_4: {}'.format(json.dumps(self.parsed_manifest_4, default=str)))


    def _parse_manifest(self, manifest_obj: ManifestBase, parsed_manifest_dict: dict, target_environments: list)->ManifestBase:
        manifest_obj.parse_manifest(
            manifest_data=parsed_manifest_dict,
            target_environments=target_environments
        )
        self.logger.info('Created final version of manifest object for manifest named "{}"'.format(manifest_obj.metadata['name']))
        return copy.deepcopy(manifest_obj)


    @mock.patch.dict(os.environ, {"DEBUG": "1"})   
    def test_unit_of_work_basic(self):
        
        for action in ('apply', 'delete',):
            for scope in ('env1', 'env2', 'env3', ):

                all_work = AllWork(logger=self.logger)

                manifests = list()
                manifests.append(self._parse_manifest(manifest_obj=MyManifest1(logger=self.logger), parsed_manifest_dict=self.parsed_manifest_1, target_environments=self.parsed_manifest_1['metadata']['environments']))
                manifests.append(self._parse_manifest(manifest_obj=MyManifest1(logger=self.logger), parsed_manifest_dict=self.parsed_manifest_2, target_environments=self.parsed_manifest_2['metadata']['environments']))
                manifests.append(self._parse_manifest(manifest_obj=MyManifest1(logger=self.logger), parsed_manifest_dict=self.parsed_manifest_3, target_environments=self.parsed_manifest_3['metadata']['environments']))
                manifests.append(self._parse_manifest(manifest_obj=MyManifest1(logger=self.logger), parsed_manifest_dict=self.parsed_manifest_4, target_environments=self.parsed_manifest_4['metadata']['environments']))
                
                # self.logger.info('manifests: {}'.format(json.dumps(manifests, default=str)))

                for manifest in manifests:
                    self.assertIsNotNone(manifest)
                    self.assertIsInstance(manifest, ManifestBase)
                    self.assertIsInstance(manifest, MyManifest1)

                    self.logger.info('Creating UnitOfWork for manifest named "{}"'.format(manifest.metadata['name']))
                    self.logger.info('    DATA: {}'.format(json.dumps(manifest.to_dict(), default=str)))

                    dependencies = list()
                    if 'dependencies' in manifest.metadata:
                        self.logger.info('        FOUND dependencies in metadata')
                        if action in manifest.metadata['dependencies']:
                            self.logger.info('        FOUND action "{}" in dependencies'.format(action))
                            dependencies = manifest.metadata['dependencies'][action]
                        else:
                            self.logger.info('        action "{}" NOT FOUND in dependencies'.format(action))
                    else: 
                        self.logger.info('        dependencies NOT FOUND in metadata')
                    self.logger.info('    dependencies "{}"'.format(dependencies))

                    run_method_name = 'apply_manifest'
                    if action == 'delete':
                        run_method_name = 'delete_manifest'
                    uow = UnitOfWork(
                        id=copy.deepcopy(manifest.metadata['name']),
                        scopes=copy.deepcopy(manifest.target_environments),
                        dependant_unit_of_work_ids=dependencies,
                        work_class=copy.deepcopy(manifest),
                        run_method_name=run_method_name,
                        logger=self.logger
                    )
                    self.assertIsNotNone(uow)

                    all_work.add_unit_of_work(unit_of_work=uow)

                self.logger.info('all_work qty of work units: {}'.format(len(all_work.all_work_list)))
                self.assertEqual(len(all_work.all_work_list), 4)

                execution_plan = ExecutionPlan(all_work=all_work, logger=self.logger)
                execution_plan.calculate_execution_plan()
                self.logger.info('Execution plan execution order: {}'.format(execution_plan.execution_order))
                self.assertIsNotNone(execution_plan.execution_order)
                self.assertIsInstance(execution_plan.execution_order, list)

                # Execute plan
                variable_cache = VariableCache()
                # manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders()
                parameters = dict()
                parameters['manifest_lookup_function'] = dummy_manifest_lookup_function
                parameters['variable_cache'] = variable_cache
                parameters['target_environment'] = scope

                execution_plan.do_work(scope=scope, **parameters)
                self.assertIsNotNone(variable_cache.values)
                self.assertIsInstance(variable_cache.values, dict)
                self.assertTrue(len(variable_cache.values) > 0)

                self.logger.info('FINAL variable_cache value: {}'.format(json.dumps(variable_cache.to_dict(), default=str)))


    def test_env_1_maintains_correct_order_event_with_adding_work_in_different_orders_for_apply_action(self):
        """
            Expected orders:

                1 -> 2 -> 4 (3 is not executed in env1)
        """
        scope = 'env1'
        manifests = list()
        manifests.append(self._parse_manifest(manifest_obj=MyManifest1(logger=self.logger), parsed_manifest_dict=self.parsed_manifest_4, target_environments=self.parsed_manifest_4['metadata']['environments']))
        manifests.append(self._parse_manifest(manifest_obj=MyManifest1(logger=self.logger), parsed_manifest_dict=self.parsed_manifest_3, target_environments=self.parsed_manifest_3['metadata']['environments']))
        manifests.append(self._parse_manifest(manifest_obj=MyManifest1(logger=self.logger), parsed_manifest_dict=self.parsed_manifest_2, target_environments=self.parsed_manifest_2['metadata']['environments']))
        manifests.append(self._parse_manifest(manifest_obj=MyManifest1(logger=self.logger), parsed_manifest_dict=self.parsed_manifest_1, target_environments=self.parsed_manifest_1['metadata']['environments']))

        all_work = AllWork(logger=self.logger)

        for manifest in manifests:

            dependencies = list()
            if 'dependencies' in manifest.metadata:
                dependencies = manifest.metadata['dependencies']['apply'] if 'apply' in manifest.metadata['dependencies'] else list()
            self.logger.info('* Dependencies for manifest named "{}": "{}"'.format(manifest.metadata['name'], dependencies))

            uow = UnitOfWork(
                id=copy.deepcopy(manifest.metadata['name']),
                scopes=copy.deepcopy(manifest.target_environments),
                dependant_unit_of_work_ids=dependencies,
                work_class=copy.deepcopy(manifest),
                run_method_name='apply_manifest',
                logger=self.logger
            )
            self.assertIsNotNone(uow)

            all_work.add_unit_of_work(unit_of_work=uow)

        execution_plan = ExecutionPlan(all_work=all_work, logger=self.logger)
        execution_plan.calculate_scoped_execution_plan(scope='env1')
        self.logger.info('Execution plan execution order: {}'.format(execution_plan.execution_order))
        self.assertIsNotNone(execution_plan.execution_order)
        self.assertIsInstance(execution_plan.execution_order, list)
        self.assertEqual(len(execution_plan.execution_order), 3)
        self.assertEqual(execution_plan.execution_order[0], 'test1')
        self.assertEqual(execution_plan.execution_order[1], 'test2')
        self.assertEqual(execution_plan.execution_order[2], 'test4')


class TestUnitOfWorkExceptionHandlingClass(unittest.TestCase):    # pragma: no cover

    @mock.patch.dict(os.environ, {"DEBUG": "1"})   
    def setUp(self):
        test_logger.messages = list()

    def test_basic_init_and_functionality_with_silent_exception(self):
        exception_handler = UnitOfWorkExceptionHandling().set_flag(flag_name='SILENT', value=True)

        result = None

        def bad_function():
            raise Exception('This will always fail')

        def test_function(eh: UnitOfWorkExceptionHandling=exception_handler):
            nonlocal result
            try:
                bad_function()
            except:
                result = eh.handle_exception(trace=traceback.extract_tb(tb=sys.exc_info()[2]), logger=test_logger)
                print('result={}'.format(result))
        
        test_function(eh=exception_handler)

        print('Logger Messages: {}'.format(test_logger.messages))
        self.assertTrue(len(test_logger.messages) == 0)
        self.assertIsNotNone(result)
        self.assertFalse(exception_handler.PASS_EXCEPTION_ON)
        self.assertFalse(result['PASS_EXCEPTION_ON'])
        self.assertTrue(result['HandledSuccessfully'])

    def test_basic_init_and_functionality_with_logging_exception(self):
        exception_handler = UnitOfWorkExceptionHandling().set_flag(flag_name='ECHO_LOGGER', value=True)

        result = None

        def bad_function():
            raise Exception('This will always fail')

        def test_function(eh: UnitOfWorkExceptionHandling=exception_handler, logger=test_logger):
            nonlocal result
            try:
                bad_function()
            except:
                result = eh.handle_exception(trace=traceback.extract_tb(tb=sys.exc_info()[2]), logger=logger)
                print('result={}'.format(result))
        
        test_function(eh=exception_handler)

        print('Logger Messages: {}'.format(test_logger.messages))
        self.assertTrue(len(test_logger.messages) > 0)
        print('Exception Message: {}'.format(test_logger.messages[0]))
        self.assertTrue('This will always fail' in test_logger.messages[0])
        self.assertIsNotNone(result)
        self.assertFalse(exception_handler.PASS_EXCEPTION_ON)
        self.assertFalse(result['PASS_EXCEPTION_ON'])
        self.assertTrue(result['HandledSuccessfully'])

    def test_basic_init_and_functionality_with_passing_on_exception(self):
        exception_handler = UnitOfWorkExceptionHandling().set_flag(flag_name='ECHO_LOGGER', value=True).set_flag(flag_name='PASS_EXCEPTION_ON', value=True)

        result = None

        def bad_function():
            raise Exception('This will always fail')

        def test_function(eh: UnitOfWorkExceptionHandling=exception_handler, logger=test_logger):
            nonlocal result
            try:
                bad_function()
            except:
                result = eh.handle_exception(trace=traceback.extract_tb(tb=sys.exc_info()[2]), logger=logger)
                print('result={}'.format(result))
        
        test_function(eh=exception_handler)

        print('Logger Messages: {}'.format(test_logger.messages))
        self.assertTrue(len(test_logger.messages) > 0)
        print('Exception Message: {}'.format(test_logger.messages[0]))
        self.assertTrue('This will always fail' in test_logger.messages[0])
        self.assertIsNotNone(result)
        self.assertTrue(exception_handler.PASS_EXCEPTION_ON)
        self.assertTrue(result['PASS_EXCEPTION_ON'])
        self.assertTrue(result['HandledSuccessfully'])
        
        


if __name__ == '__main__':
    unittest.main()
