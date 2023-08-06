"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""
import traceback
import copy
from py_animus import get_logger


class UnitOfWork:

    def __init__(self, id: str, scopes: list, dependant_unit_of_work_ids: list, work_class: object, run_method_name: str='apply', logger=get_logger()):
        self.id = id
        self.scopes = scopes
        self.dependencies = dependant_unit_of_work_ids
        self.work_class = work_class
        self.run_method_name = run_method_name
        self.logger = logger

    def run(self, **kwargs):

        parameters = dict()
        for k,v in kwargs.items():
            parameters[k] = v

        self.logger.info('UnitOfWork: ID={}'.format(self.id))
        self.logger.info('UnitOfWork:    kwargs={}'.format(parameters))
        try:
            getattr(self.work_class, self.run_method_name)(**parameters)
        except:
            traceback.print_exc()


class AllWork:

    def __init__(self, logger=get_logger()):
        self.all_work_list = list()
        self.logger = logger

    def unit_of_work_by_id_exists(self, id: str)->bool:
        for uow in self.all_work_list:
            if uow.id == id:
                return True
        return False

    def add_unit_of_work(self, unit_of_work: UnitOfWork):
        if self.unit_of_work_by_id_exists(id=unit_of_work.id) is False:
            self.all_work_list.append(unit_of_work)


    def get_unit_of_work_by_id(self, id: str)->UnitOfWork:
        for uow in self.all_work_list:
            if uow.id == id:
                return uow


class ExecutionPlan:

    def __init__(self, all_work:AllWork, logger=get_logger()):
        self.all_work = all_work
        self.execution_order = list()
        self.logger = logger

    def add_unit_of_work_to_execution_order(self, uow: UnitOfWork):
        for parent_uow_id in uow.dependencies:
            if parent_uow_id not in self.execution_order:
                self.add_unit_of_work_to_execution_order(uow=self.all_work.get_unit_of_work_by_id(id=parent_uow_id))
        if uow.id not in self.execution_order:
            self.execution_order.append(uow.id)

    def calculate_execution_plan(self):
        self.execution_order = list()
        for uow in self.all_work.all_work_list:
            self.add_unit_of_work_to_execution_order(uow=uow)

    def calculate_scoped_execution_plan(self, scope: str):
        final_execution_order = list()
        self.calculate_execution_plan()
        current_execution_order = copy.deepcopy(self.execution_order)
        for uof_id in current_execution_order:
            uow = self.all_work.get_unit_of_work_by_id(id=uof_id)
            if scope in uow.scopes:
                final_execution_order.append(uof_id)
        self.execution_order = copy.deepcopy(final_execution_order)

    def do_work(self, scope: str, **kwargs):
        self.calculate_execution_plan()
        
        parameters = dict()
        for k,v in kwargs.items():
            parameters[k] = v

        for uof_id in self.execution_order:
            uow = self.all_work.get_unit_of_work_by_id(id=uof_id)
            if scope in uow.scopes:
                uow.run(**parameters)
        self.execution_order = list()