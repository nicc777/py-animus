"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

from py_animus import get_logger, get_utc_timestamp, is_debug_set_in_environment
import copy


class Variable:

    def __init__(self, name: str, initial_value=None, ttl: int=-1, logger=get_logger()):
        self.name = name
        self.value = initial_value
        self.ttl = ttl
        self.init_timestamp = get_utc_timestamp(with_decimal=False)
        self.debug = is_debug_set_in_environment()
        self.logger = logger

    def _log_debug(self, message):
        if self.debug is True:
            self.logger.debug('[{}:{}] {}'.format(self.__class__.__name__, self.name, message))

    def set_value(self, value, reset_ttl: bool=True):
        self.value = value
        if reset_ttl is True:
            self._log_debug(message='Resetting timers')
            self.init_timestamp = get_utc_timestamp(with_decimal=False)

    def _is_expired(self):
        if self.ttl < 0:
            self._log_debug(message='NOT EXPIRED - TTL less than zero - expiry ignored')
            return False
        elapsed_time = get_utc_timestamp(with_decimal=False) - self.init_timestamp
        self._log_debug(message='elapsed_time={}'.format(elapsed_time))
        if elapsed_time > self.ttl:
            self._log_debug(message='EXPIRED')
            return True
        self._log_debug(message='NOT EXPIRED')
        return False

    def get_value(self, value_if_expired=None, raise_exception_on_expired: bool=True, reset_timer_on_value_read: bool=False):
        if self._is_expired() is True:
            if raise_exception_on_expired is True:
                raise Exception('Expired')
            self._log_debug(message='Expired, but alternate value supplied. Returning alternate value.')
            return value_if_expired
        if reset_timer_on_value_read is True:
            self._log_debug(message='Resetting timers')
            self.init_timestamp = get_utc_timestamp(with_decimal=False)
        self._log_debug(message='Returning value')
        return self.value


class VariableCache:

    def __init__(self, logger=get_logger()):
        self.values = dict()
        self.logger = logger

    def store_variable(self, variable: Variable, overwrite_existing: bool=False):
        if variable.name not in self.values or overwrite_existing is True:
            self.values[variable.name] = variable

    def get_value(self, variable_name: str, value_if_expired=None, raise_exception_on_expired: bool=True, reset_timer_on_value_read: bool=False):
        if variable_name not in self.values:
            raise Exception('Variable "{}" not found'.format(variable_name))
        return copy.deepcopy(self.values[variable_name].get_value(value_if_expired=value_if_expired, raise_exception_on_expired=raise_exception_on_expired, reset_timer_on_value_read=reset_timer_on_value_read))


