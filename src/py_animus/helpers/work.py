"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""
import traceback
import copy
import sys
from py_animus import get_logger


class UnitOfWorkExceptionHandling:
    """
        Class to assist with UnitOfWork error handling.

        The following flags are defined:

            SILENT: Do not print or log anything
            ECHO_TRACEBACK: Dump the stacktrace using the Python built in traceback functionality for this
            ECHO_LOGGER: Use the logger (if set) to log the exception stack trace
            PASS_EXCEPTION_ON: If set to True, a new Exception will be raised to be handled by the calling party.

        In addition, the following values are set:

            LOGGER: The logger class
            LEVEL: The level to use when using the LOGGER class
    """

    SILENT = False
    ECHO_TRACEBACK = True
    ECHO_LOGGER = False
    PASS_EXCEPTION_ON = False
    LOGGER = None
    LEVEL = 'error'

    def set_flag(self, flag_name: str, value: bool):
        """Sets one of the flags and returns a copy of the class instance

        Examples:

            # Use defaults:
            >>> t = UnitOfWorkExceptionHandling()   

            # Sets the SILENT flag value:
            >>> t = UnitOfWorkExceptionHandling().set_flag(flag_name='SILENT', value=False)

            # Sets both the SILENT and ECHO_TRACEBACK flag values:
            >>> t = UnitOfWorkExceptionHandling().set_flag(flag_name='SILENT', value=True).set_flag(flag_name='ECHO_TRACEBACK', value=False)

        Args:
            flag_name: (str) One of 'SILENT', 'ECHO_TRACEBACK', 'ECHO_LOGGER' or 'PASS_EXCEPTION_ON'
            value: (bool) The flag value (True or False)

        Returns:
            A copy of Self

        Raises:
            Exception: On validation errors of input parameters
        """
        if value is None:
            raise Exception('value cannot be None')
        if isinstance(value, bool) is False:
            raise Exception('value must be a boolean type')
        if flag_name.upper() not in ('SILENT', 'ECHO_TRACEBACK', 'ECHO_LOGGER', 'PASS_EXCEPTION_ON',):
            raise Exception('unrecognized flag_name')
        if flag_name.upper() == 'SILENT':
            self.SILENT = value
        if flag_name.upper() == 'ECHO_TRACEBACK':
            self.ECHO_TRACEBACK = value
        if flag_name.upper() == 'ECHO_LOGGER':
            self.ECHO_LOGGER = value
        if flag_name.upper() == 'PASS_EXCEPTION_ON':
            self.PASS_EXCEPTION_ON = value
        return self

    def set_level(self, level: str):
        """Sets the logging level

        Examples:

            # Use defaults:
            >>> t = UnitOfWorkExceptionHandling()   

            # Sets logging level to "ino":
            >>> t = UnitOfWorkExceptionHandling().set_level(level='info')

            # Sets both the SILENT and ECHO_TRACEBACK flag values as well as the logging level:
            >>> t = UnitOfWorkExceptionHandling().set_flag(flag_name='SILENT', value=True).set_flag(flag_name='ECHO_TRACEBACK', value=False).set_level(level='info')

        Args:
            level: (str) One of 'info', 'debug', 'error' or 'warning'

        Returns:
            A copy of Self

        Raises:
            Exception: On validation errors of input parameters
        """
        if level is None:
            raise Exception('level cannot be None')
        if isinstance(level, str) is False:
            raise Exception('level must be a string type')
        if level.lower() not in ('info', 'debug', 'error', 'warn', 'warning'):
            raise Exception('unrecognized level')
        if level.lower().startswith('i'):
            self.LEVEL = 'info'
        if level.lower().startswith('d'):
            self.LEVEL = 'debug'
        if level.lower().startswith('e'):
            self.LEVEL = 'error'
        if level.lower().startswith('w'):
            self.LEVEL = 'warning'
        return self
    
    def set_logger_class(self, logger):
        """Sets the logging level

        Examples:

            # Use defaults:
            >>> t = UnitOfWorkExceptionHandling()   

            # Sets logging level to "ino":
            >>> t = UnitOfWorkExceptionHandling().set_level(level='info')

            # Sets both the SILENT and ECHO_TRACEBACK flag values as well as the logging level:
            >>> t = UnitOfWorkExceptionHandling().set_flag(flag_name='SILENT', value=True).set_flag(flag_name='ECHO_TRACEBACK', value=False).set_logger_class(logger=.....)

        Args:
            logger: (object) A logging implementation that implements all of these methods: 'info', 'debug', 'error' and 'warning'

        Returns:
            A copy of Self

        Raises:
            Exception: On validation errors of input parameters
        """
        if logger is None:
            raise Exception('logger cannot be None')
        self.LOGGER = logger
        return self

    def _handle_echo_traceback(self, trace)->bool:
        if self.ECHO_TRACEBACK is True:
            try:
                trace.print_exc()
            except:
                return False
        return True
    
    def _handle_echo_logger(self, trace)->bool:
        if self.ECHO_LOGGER is True:
            try:
                if self.LOGGER is not None:
                    getattr(self.LOGGER, self.LEVEL)('EXCEPTION: {}'.format(traceback.format_exc()))
            except:
                return False
        return True

    def handle_exception(self, trace)->dict:
        handled_successfully = False
        flag_values = {
            'SILENT'            : self.SILENT,
            'ECHO_TRACEBACK'    : self.ECHO_TRACEBACK,
            'ECHO_LOGGER'       : self.ECHO_LOGGER,
            'PASS_EXCEPTION_ON' : self.PASS_EXCEPTION_ON,
            'LOGGER'            : True if self.LOGGER is not None else False,
            'LEVEL'             : self.LEVEL
        }

        if self.SILENT is True:
            handled_successfully = True
        else:
            if self.ECHO_TRACEBACK is True:
                handled_successfully = self._handle_echo_traceback(trace=trace)
            if self.ECHO_LOGGER is True:
                handled_successfully = self._handle_echo_logger(trace=trace)

        flag_values['HandledSuccessfully'] = handled_successfully
        return flag_values


class UnitOfWork:

    def __init__(
            self,
            id: str,
            scopes: list,
            dependant_unit_of_work_ids: list,
            work_class: object,
            run_method_name: str='apply_manifest',
            logger=get_logger(),
            exception_handling: UnitOfWorkExceptionHandling=UnitOfWorkExceptionHandling()
        ):
        self.id = id
        self.scopes = scopes
        self.dependencies = dependant_unit_of_work_ids
        self.work_class = work_class
        self.run_method_name = run_method_name
        self.logger = logger
        self.exception_handling = exception_handling

    def run(self, **kwargs):

        parameters = dict()
        for k,v in kwargs.items():
            parameters[k] = v

        self.logger.info('UnitOfWork: ID={}'.format(self.id))
        self.logger.info('UnitOfWork:    kwargs={}'.format(parameters))
        exception_result =dict()
        try:
            getattr(self.work_class, self.run_method_name)(**parameters)
        # except:
        #     traceback.print_exc()
        except Exception as e:
            exc_type, exc_value, exc_tb = sys.exc_info()
            tb = traceback.TracebackException(exc_type, exc_value, exc_tb)
            exception_result = self.exception_handling.handle_exception(trace=tb, logger=self.logger)

        if len(exception_result) > 0:
            if 'HandledSuccessfully' in exception_result:
                if exception_result['HandledSuccessfully'] is False:
                    self.logger.warning('The exception was caught but something went wrong with the exception handling.')
            if 'PASS_EXCEPTION_ON' in exception_result:
                if exception_result['PASS_EXCEPTION_ON'] is True:
                    raise Exception('UnitOfWork "{}" threw an exception and configuration forced this exception to be raised to halt further processing.'.format(self.id))


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

    def __init__(self, all_work:AllWork, logger=get_logger(), stop_on_exception: bool=True):
        self.all_work = all_work
        self.execution_order = list()
        self.logger = logger
        self.exception_handler = UnitOfWorkExceptionHandling().set_logger_class(logger=logger)
        self.stop_on_exception = stop_on_exception

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

                exception_raised = False
                try:
                    uow.run(**parameters)
                except:
                    result = self.exception_handler.handle_exception(trace=traceback.extract_tb(tb=sys.exc_info()[2]))
                    self.logger.error('UnitOfWork named "{}" failed with Exception. UnitOfWorkExceptionHandling result: {}'.format(uow.id, result))
                    exception_raised = True

                if exception_raised is True and self.stop_on_exception is True:
                    raise Exception('Cannot continue further due to UnitOfWork named "{}" that threw exception'.format(uow.id))
                elif exception_raised is True and self.stop_on_exception is False:
                    self.logger.warning('UnitOfWork named "{}" that threw exception, but configuration insist that work carries on'.format(uow.id))
                
        self.execution_order = list()