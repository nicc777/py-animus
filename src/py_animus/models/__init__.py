"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""
import traceback
import copy
import json
import logging
from py_animus.helpers import get_utc_timestamp, is_debug_set_in_environment


class Value:

    def __init__(self, name: str, initial_value: object):
        self.name = name
        self.value = initial_value

    def update_value(self, new_value: object):
        self.value = new_value


class Values:

    def __init__(self):
        self.values = dict()

    def add_value(self, value: Value):
        self.values[value.name] = value

    def find_value_by_name(self, name: str)->Value:
        if name not in self.values:
            raise Exception('Value named "{}" was not found'.format(name))
        return self.values[name]
    
    def remove_value(self, name: str):
        if name in self.values:
            self.values.pop(name)


class ScopedValues:

    def __init__(self, scope: str):
        self.scope = scope
        self.values = Values()

    def add_value(self, value: Value):
        self.values.add_value(value=value)

    def find_value_by_name(self, name: str)->Value:
        return self.values.find_value_by_name(name=name)
    
    def remove_value(self, name: str):
        self.values.remove_value(name=name)


class AllScopedValues:

    def __init__(self) -> None:
        self.scoped_values_collection = dict()

    def add_scoped_values(self, scoped_values: ScopedValues, replace: bool=False):
        if scoped_values.scope not in self.scoped_values_collection:
            self.scoped_values_collection[scoped_values.scope] = scoped_values
        else:
            if replace is True:
                self.scoped_values_collection[scoped_values.scope] = scoped_values

    def find_scoped_values(self, scope: str)->ScopedValues:
        if scope not in self.scoped_values_collection:
            raise Exception('ScopedValues for scope "{}" Not Found'.format(scope))
        return self.scoped_values_collection[scope]
        
    def add_value_to_scoped_value(self, scope: str, value: Value):
        current_scoped_values = self.find_scoped_values(scope=scope)
        current_scoped_values.add_value(value=value)
        self.add_scoped_values(scoped_values=copy.deepcopy(current_scoped_values), replace=True)


class Variable:
    """A Variable is a runtime value generated by some operation that will be stored in a VariableCache in the 
    ManifestManager. Any other operation launched from the ManifestManager will have access to the current runtime 
    sVariable values.

    Within the user implementation of some class that extends ManifestBase, a method called apply_manifest() can update
    the VariableCache with a new Variable or change the value of an existing Variable.

    Example:

    >>> variable_cache.store_variable(variable=Variable(name='some-name', initial_value='Another value worth storing'))

    Example of overwriting an existing Variable value:

    >>> variable_cache.store_variable(variable=Variable(name='some-name', initial_value='Overriding some existing value...'), overwrite_existing=True)

    Attributes:
        name: A String with the Variable name.
        initial_value: Any object containing a any value
        ttl: Integer with the time to live for the variable value in the cache (in seconds, default is -1 or unlimited lifespan while the application is running)
        mask_in_logs: A boolean to indicate if the value is sensitive and that it should be masked in logs
    """

    def __init__(self, name: str, initial_value=None, ttl: int=-1, mask_in_logs: bool=False):
        """Initializes a new instance of a Variable to be stored in the VariableCache.

        Args:
          name: String with a unique name of this variable. (Will be validated as unique in VariableCache)
          initial_value: Object storing some initial value (Optional, default=None)
          ttl: Integer of seconds for Variable's value to be considered valid in the context of the VariableCache. (Optional, default=-1 which never expires)
        """
        self.name = name
        self.value = initial_value
        self.ttl = ttl
        self.init_timestamp = get_utc_timestamp(with_decimal=False)
        self.debug = is_debug_set_in_environment()
        self.mask_in_logs = mask_in_logs

    def _log_debug(self, message):
        if self.debug is True:
            logging.debug('[{}:{}] {}'.format(self.__class__.__name__, self.name, message))

    def set_value(self, value, reset_ttl: bool=True):
        """Set the value of the Variable.

        Args:
          value: Object storing some value (required)
          reset_ttl: Boolean to indicate of the timers of TTL must be reset (optional, default=True)
        """
        self.value = value
        if reset_ttl is True:
            self._log_debug(message='Resetting timers')
            self.init_timestamp = get_utc_timestamp(with_decimal=False)

    def _is_expired(self):
        if self.ttl < 0:
            self._log_debug(message='NOT EXPIRED - TTL less than zero - expiry ignored')
            return False
        elapsed_time = get_utc_timestamp(with_decimal=False) - self.init_timestamp
        self._log_debug(message='elapsed_time={}   ttl={}'.format(elapsed_time, self.ttl))
        if elapsed_time > self.ttl:
            self._log_debug(message='EXPIRED')
            return True
        self._log_debug(message='NOT EXPIRED')
        return False

    def get_value(self, value_if_expired=None, raise_exception_on_expired: bool=True, reset_timer_on_value_read: bool=False, for_logging: bool=False):
        """Get the value of the Variable.

        To get more granular logging, enable debug by setting an environment variable DEBUG to "1"

        Args:
          value_if_expired: What to return if the value is considered expired (Optional, default=None as by default an Exception will be raised)
          raise_exception_on_expired: Boolean to indicate an Exception must be thrown if the value is considered expired (optional, default=True)
          reset_timer_on_value_read: Boolean to reset timers for expiry is the value is read (Optional, default=False)

        Returns:
            The value

        Raises:
            Exception: When the value has expired
        """
        final_value = None
        if self.value is not None:
            final_value = copy.deepcopy(self.value)
        if self._is_expired() is True:
            if raise_exception_on_expired is True:
                raise Exception('Expired')
            self._log_debug(message='Expired, but alternate value supplied. Returning alternate value.')
            final_value = copy.deepcopy(value_if_expired)
        elif reset_timer_on_value_read is True:
            self._log_debug(message='Resetting timers')
            self.init_timestamp = get_utc_timestamp(with_decimal=False)
        self._log_debug(message='Returning value')

        if final_value is not None:
            if self.mask_in_logs is True and for_logging is True and isinstance(final_value, str):
                final_value = '*' * len(final_value)
            elif self.mask_in_logs is True and for_logging is True:
                final_value = '***'

        return final_value
    
    def log_value(self, value_if_expired=None, raise_exception_on_expired: bool=True, reset_timer_on_value_read: bool=False):
        value = self.get_value(value_if_expired=value_if_expired, raise_exception_on_expired=raise_exception_on_expired, reset_timer_on_value_read=reset_timer_on_value_read, for_logging=True)
        if is_debug_set_in_environment() is True:
            logging.debug('Variable(name="{}", init_timestamp={}, ttl={}, mask_in_logs={}): "{}"'.format(self.name, self. init_timestamp, self.ttl, self.mask_in_logs, value))
        else:
            logging.info('Variable(name="{}"): "{}"'.format(self.name, value))
    
    def to_dict(self, for_logging: bool=False):
        final_value = ''
        if self.value is not None:
            final_value = '{}'.format(str(self.value))
            if self.mask_in_logs is True and for_logging is True and isinstance(final_value, str):
                final_value = '*' * len(final_value)
            elif self.mask_in_logs is True and for_logging is True:
                final_value = '***'
        data = {
            'ttl': self.ttl,
            'value': final_value,
            'expires': self.ttl + self.init_timestamp,
        }
        if self.ttl < 0:
            data['expires'] = 9999999999
        return data


class VariableCache:
    """A VariableCache holds a collection of Variable instances

    Attributes:
        values: Dictionary of Variable instance, index by each Variable name
    """

    def __init__(self):
        """Initializes a new instance of a VariableCache hold a collection of Variable instances.

        Args:
          logger: An instance of logging.Logger used for logging (Optional, default is teh result from internal call to get_logger())
        """
        self.values = dict()

    def store_variable(self, variable: Variable, overwrite_existing: bool=False):
        """Stores an instance of Variable

        If the Variable already exist (by name), and `overwrite_existing` is False, effectively nothing is done.

        Args:
          variable: An instance of Variable
          overwrite_existing: Boolean to indicate if a any pre-existing Variable (with the same name) must be over written with this value. (Optional, Default=False)
        """
        if variable.name not in self.values or overwrite_existing is True:
            self.values[variable.name] = variable

    def get_value(
            self,
            variable_name: str, 
            value_if_expired=None, 
            raise_exception_on_expired: bool=True, 
            reset_timer_on_value_read: bool=False,
            raise_exception_on_not_found: bool=True,
            default_value_if_not_found=None,
            for_logging: bool=False
        ):
        """Get the value of a stored Variable.

        To get more granular logging, enable debug by setting an environment variable DEBUG to "1"

        Args:
          variable_name: String with the name of a previously stored Variable
          value_if_expired: What to return if the value is considered expired (Optional, default=None as by default an Exception will be raised)
          raise_exception_on_expired: Boolean to indicate an Exception must be thrown if the value is considered expired (optional, default=True)
          reset_timer_on_value_read: Boolean to reset timers for expiry is the value is read (Optional, default=False)
          raise_exception_on_not_found: Boolean to determine if an exception is raised when the named variable is not found (optional, default=True)
          default_value_if_not_found: Any default value that can be returned if `raise_exception_on_not_found` is set to `False` (optional, default=None)

        Returns:
            A copy of the value stored in Variable with the given name, or whatever is set in 
            `default_value_if_not_found` if `raise_exception_on_not_found` is False and the named `Variable` was not
            found. If the `Variable` has expired, the value of `value_if_expired` will be returned if 
            `raise_exception_on_expired` is False.

        Raises:
            Exception: When the value has expired (From Variable) (pass through), and if `raise_exception_on_expired` is True
            Exception: When the Variable is not found, and if `raise_exception_on_not_found` is True
        """
        if variable_name not in self.values and raise_exception_on_not_found is True:
            logging.debug('[variable_name={}] Variable NOT FOUND, and raise_exception_on_not_found is set to True'.format(variable_name))
            raise Exception('Variable "{}" not found'.format(variable_name))
        elif variable_name not in self.values and raise_exception_on_not_found is False:
            logging.debug('[variable_name={}] Variable NOT FOUND, and raise_exception_on_not_found is set to False - Returning default_value_if_not_found'.format(variable_name))
            return default_value_if_not_found
        return copy.deepcopy(self.values[variable_name].get_value(value_if_expired=value_if_expired, raise_exception_on_expired=raise_exception_on_expired, reset_timer_on_value_read=reset_timer_on_value_read, for_logging=for_logging))

    def delete_variable(self, variable_name: str):
        if variable_name in self.values:
            logging.debug('[variable_name={}] Deleted'.format(variable_name))
            self.values.pop(variable_name)

    def to_dict(self, for_logging: bool=False):
        data = dict()
        for k,v in self.values.items():
            v_dict = v.to_dict(for_logging=for_logging)
            data[k] = v_dict
        return data

    def __str__(self)->str:
        return json.dumps(self.to_dict(for_logging=True))
    

all_scoped_values = AllScopedValues()
variable_cache = VariableCache()
scope = 'default'
