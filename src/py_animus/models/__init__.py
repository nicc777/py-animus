"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""
import copy
import json
import importlib
# from py_animus.animus_logging import logger
import py_animus.animus_logging as animus_logger
from py_animus.helpers import get_utc_timestamp, is_debug_set_in_environment


class LoggerHelper:

    def __init__(self):
        self.logger_is_initialized = False
        self.logger = None

    def initialize(self):
        if self.logger_is_initialized is False:
            importlib.reload(animus_logger)
            self.logger = animus_logger.logger

    def log_info(self, message: str):
        self.initialize()
        self.logger.info(message)

    def log_debug(self, message: str):
        self.initialize()
        self.logger.debug(message)

    def log_error(self, message: str):
        self.initialize()
        self.logger.error(message)

    def log_warning(self, message: str):
        self.initialize()
        self.logger.warning(message)

    def log_warn(self, message: str):
        self.log_warning(message=message)

    def reload_logger(self):
        importlib.reload(animus_logger)
        self.logger = animus_logger.logger


class Action:

    UNKNOWN                     = 'UNKNOWN'
    NO_ACTION                   = 'NO_ACTION'
    APPLY_PENDING               = 'APPLY_PENDING'
    APPLY_DONE                  = 'APPLY_DONE'
    APPLY_ABORTED_WITH_ERRORS   = 'APPLY_ABORTED_WITH_ERRORS'
    APPLY_CREATE_NEW            = 'APPLY_CREATE_NEW'
    APPLY_UPDATE_EXISTING       = 'APPLY_UPDATE_EXISTING'
    APPLY_DELETE_EXISTING       = 'APPLY_DELETE_EXISTING'
    APPLY_SKIP                  = 'APPLY_SKIP'
    DELETE_PENDING              = 'DELETE_PENDING'
    DELETE_DONE                 = 'DELETE_DONE'
    DELETE_ABORTED_WITH_ERRORS  = 'DELETE_ABORTED_WITH_ERRORS'
    DELETE_DELETE_EXISTING      = 'DELETE_DELETE_EXISTING'
    DELETE_SKIP                 = 'DELETE_SKIP'
    _possible_actions = (
        'UNKNOWN',
        'NO_ACTION',
        'APPLY_PENDING',
        'APPLY_DONE',
        'APPLY_ABORTED_WITH_ERRORS',
        'APPLY_CREATE_NEW',
        'APPLY_UPDATE_EXISTING',
        'APPLY_DELETE_EXISTING',
        'APPLY_SKIP',
        'DELETE_PENDING',
        'DELETE_DONE',
        'DELETE_ABORTED_WITH_ERRORS',
        'DELETE_DELETE_EXISTING',
        'DELETE_SKIP',
    )

    def __init__(self, manifest_kind: str, manifest_name: str, action_name: str, action_status: str):
        if action_status not in self._possible_actions:
            raise Exception('Unsupported Action Status "{}"'.format(action_status))
        self.current_status = action_status
        self.kind = manifest_kind
        self.name = manifest_name
        self.action_name = action_name

    def update_action_status(self, new_action_status: str):
        if new_action_status not in self._possible_actions:
            raise Exception('Unsupported Action Status "{}"'.format(new_action_status))
        self.current_status = new_action_status

    def get_status(self):
        return self.current_status


class Actions:

    _actions_considered_completed = (
        'NO_ACTION',
        'APPLY_DONE',
        'APPLY_ABORTED_WITH_ERRORS',
        'APPLY_SKIP',
        'APPLY_DONE',
        'APPLY_ABORTED_WITH_ERRORS',
        'APPLY_SKIP',
    )

    APPLY = 'apply'
    DELETE = 'delete'

    def __init__(self):
        self.actions = dict()
        self.progress = 0.0
        self.command = 'unknown'

    def set_command(self, command: str):
        if command not in (self.APPLY, self.DELETE, ):
            raise Exception('Unsupported command "{}"'.format(command))
        self.command = command

    def _update_progress(self):
        if len(self.actions) > 0:
            done_count = 0
            for idx, action in self.actions.items():
                for complete_action in self._actions_considered_completed:
                    if complete_action == action.current_status:
                        done_count += 1
            self.progress = done_count / len(self.actions)
        else:
            self.progress = 0.0

    def add_or_update_action(self, action: Action):
        idx = '{}:{}:{}'.format(action.kind, action.name, action.action_name)
        self.actions[idx] = action
        self._update_progress()

    def get_action_names(self, manifest_kind: str, manifest_name: str)->tuple:
        action_names = list()
        for key in list(self.actions.keys()):
            a_kind, a_name, a_action_name = key.split(':')
            if a_kind == manifest_kind and a_name == manifest_name:
                action_names.append(a_action_name)
        return tuple(action_names)
    
    def get_action_values_for_manifest(self, manifest_kind: str, manifest_name: str)->dict:
        found_actions = dict()
        for a_action_name in self.get_action_names(manifest_kind=manifest_kind, manifest_name=manifest_name):
            try:
                found_actions[a_action_name] = self.get_action_status(manifest_kind=manifest_kind, manifest_name=manifest_name, action_name=a_action_name)
            except:
                found_actions[a_action_name] = Action.NO_ACTION
        return found_actions

    def get_action_status(self, manifest_kind: str, manifest_name: str, action_name: str)->str:
        idx = '{}:{}:{}'.format(manifest_kind, manifest_name, action_name)
        if idx not in self.actions:
            return Action.UNKNOWN
        return self.actions[idx].current_status
    
    def get_progress(self)->float:
        return self.progress
    
    def get_progress_percentage(self)->float:
        return self.progress * 100.0


actions = Actions()


class Value:

    def __init__(self, name: str, initial_value: object):
        self.name = name
        self.value = initial_value

    def update_value(self, new_value: object):
        self.value = new_value


class Values:

    def __init__(self):
        self.values = dict()
        self.log_helper = LoggerHelper()

    def add_value(self, value: Value):
        self.values[value.name] = value
        self.log_helper.log_debug('Added value {}'.format(value.name))

    def find_value_by_name(self, name: str)->Value:
        if name not in self.values:
            self.log_helper.log_error('Dump of current values keys: {}'.format(list(self.values.keys())))
            return Value(name=name, initial_value=None)
        return self.values[name]
    
    def remove_value(self, name: str):
        if name in self.values:
            self.values.pop(name)

    def reset_logger(self):
        self.log_helper = LoggerHelper()
        self.log_helper.reload_logger()


class ScopedValues:

    def __init__(self, scope: str):
        self.scope = scope
        self.values = Values()
        self.log_helper = LoggerHelper()

    def add_value(self, value: Value):
        self.values.add_value(value=value)
        self.log_helper.log_debug('   Added value {} for scope {}'.format(value.name, self.scope))

    def find_value_by_name(self, name: str)->Value:
        return self.values.find_value_by_name(name=name)
    
    def remove_value(self, name: str):
        self.values.remove_value(name=name)

    def reset_logger(self):
        self.log_helper = LoggerHelper()
        self.log_helper.reload_logger()
        self.values.reset_logger()


class AllScopedValues:

    def __init__(self) -> None:
        self.scoped_values_collection = dict()
        self.log_helper = LoggerHelper()

    def add_scoped_values(self, scoped_values: ScopedValues, replace: bool=False):
        if scoped_values.scope not in self.scoped_values_collection:
            self.scoped_values_collection[scoped_values.scope] = scoped_values
        else:
            if replace is True:
                self.scoped_values_collection[scoped_values.scope] = scoped_values
        self.log_helper.log_debug('Added scoped values for scope {}'.format(scoped_values.scope))

    def find_scoped_values(self, scope: str)->ScopedValues:
        if scope not in self.scoped_values_collection:
            empty_scoped_values = ScopedValues(scope=scope)
            return empty_scoped_values
        return self.scoped_values_collection[scope]
        
    def add_value_to_scoped_value(self, scope: str, value: Value):
        current_scoped_values = self.find_scoped_values(scope=scope)
        current_scoped_values.add_value(value=value)
        self.add_scoped_values(scoped_values=copy.deepcopy(current_scoped_values), replace=True)
        self.log_helper.log_debug('Scoped value named "{}" added for scope "{}"'.format(value.name, scope))

    def clear(self):
        self.scoped_values_collection = dict()

    def reset_logger(self):
        self.log_helper = LoggerHelper()
        self.log_helper.reload_logger()
        for scope, scoped_values in self.scoped_values_collection.items():
            scoped_values.reset_logger()


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
        self.log_helper = LoggerHelper()

    def _log_debug(self, message):
        if self.debug is True:
            self.log_helper.log_debug('[{}:{}] {}'.format(self.__class__.__name__, self.name, message))

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
            self.log_helper.log_debug('Variable(name="{}", init_timestamp={}, ttl={}, mask_in_logs={}): "{}"'.format(self.name, self. init_timestamp, self.ttl, self.mask_in_logs, value))
        else:
            self.log_helper.log_info('Variable(name="{}"): "{}"'.format(self.name, value))
    
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
    
    def reset_logger(self):
        self.log_helper = LoggerHelper()
        self.log_helper.reload_logger()


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
        self.log_helper = LoggerHelper()

    def get_all_variable_names_staring_with(self, start_str: str)->list:
        names = list()
        for values_key in list(self.values.keys()):
            if values_key.startswith(start_str):
                names.append(values_key)
        return names

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
            init_with_default_value_if_not_found: bool=False,
            for_logging: bool=False,
            unresolved_variables_returns_original_reference: bool=True
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
        if variable_name not in self.values and init_with_default_value_if_not_found is True:
            self.store_variable(
                variable=Variable(
                    name=variable_name,
                    initial_value=default_value_if_not_found
                )
            )
        if variable_name not in self.values and raise_exception_on_not_found is True:
            self.log_helper.log_debug('[variable_name={}] Variable NOT FOUND, and raise_exception_on_not_found is set to True'.format(variable_name))
            if unresolved_variables_returns_original_reference is True:
                self.log_helper.log_debug('[variable_name={}] unresolved_variables_returns_original_reference was TRUE - returning: !Variable {}'.format(variable_name, variable_name))
                return '!Variable {}'.format(variable_name)
                # return PendingVariable(original_variable_name=variable_name)
            else:
                raise Exception('Variable "{}" not found'.format(variable_name))
        elif variable_name not in self.values and raise_exception_on_not_found is False:
            self.log_helper.log_debug('[variable_name={}] Variable NOT FOUND, and raise_exception_on_not_found is set to False - Returning default_value_if_not_found: {}'.format(variable_name, default_value_if_not_found))
            return default_value_if_not_found
        final_value = copy.deepcopy(self.values[variable_name].get_value(value_if_expired=value_if_expired, raise_exception_on_expired=raise_exception_on_expired, reset_timer_on_value_read=reset_timer_on_value_read, for_logging=for_logging))
        self.log_helper.log_debug('[variable_name={}] final_value: {}'.format(variable_name, final_value))
        return final_value

    def add_dict_item_to_existing_variable(
            self,
            variable_name: str,
            key: str,
            value: object,
            ignore_if_already_exists: bool=False,
            raise_exception_if_value_type_is_not_a_dict: bool=True
        )->dict:
        update_value = False
        if variable_name in self.values:
            current_value = copy.deepcopy(self.values[variable_name].get_value(value_if_expired=dict(), raise_exception_on_expired=False, reset_timer_on_value_read=False, for_logging=False))
            if isinstance(current_value, dict) is True:
                if key in current_value:
                    if ignore_if_already_exists is False:
                        update_value = True
                else:
                    update_value = True
                if update_value is True:
                    current_value[key] = value
                    self.store_variable(
                        variable=Variable(
                            name=variable_name,
                            initial_value=current_value
                        ),
                        overwrite_existing=True
                    )
            else:
                if raise_exception_if_value_type_is_not_a_dict is True:
                    raise Exception('Expected a dict type variable')
                return dict()
        else:
            self.store_variable(
                variable=Variable(
                    name=variable_name,
                    initial_value={key: value}
                )
            )
        return copy.deepcopy(self.values[variable_name].get_value(value_if_expired=dict(), raise_exception_on_expired=False, reset_timer_on_value_read=True, for_logging=False))
    
    def add_list_item_to_existing_variable(self, variable_name: str, value: object, ignore_if_already_exists: bool=False, raise_exception_if_value_type_is_not_a_list: bool=True)->dict:
        if variable_name in self.values:
            current_value = copy.deepcopy(self.values[variable_name].get_value(value_if_expired=dict(), raise_exception_on_expired=False, reset_timer_on_value_read=False, for_logging=False))
            if isinstance(current_value, list) is True:
                current_value.append(value)
                self.store_variable(
                    variable=Variable(
                        name=variable_name,
                        initial_value=current_value
                    ),
                    overwrite_existing=True
                )
            else:
                if raise_exception_if_value_type_is_not_a_list is True:
                    raise Exception('Expected a dict type variable')
                return list()
        else:
            self.store_variable(
                variable=Variable(
                    name=variable_name,
                    initial_value=[value,]
                )
            )
        return self.get_value(variable_name=variable_name)

    def delete_variable(self, variable_name: str):
        if variable_name in self.values:
            self.log_helper.log_debug('[variable_name={}] Deleted'.format(variable_name))
            self.values.pop(variable_name)

    def to_dict(self, for_logging: bool=False):
        data = dict()
        for k,v in self.values.items():
            v_dict = v.to_dict(for_logging=for_logging)
            data[k] = v_dict
        return data

    def __str__(self)->str:
        return json.dumps(self.to_dict(for_logging=True))
    
    def clear(self):
        self.values = dict()

    def reset_logger(self):
        self.log_helper = LoggerHelper()
        self.log_helper.reload_logger()
        for variable_name, variable in self.values.items():
            variable.reset_logger()

    def get_all_current_names(self):
        return list(self.values.keys())
    

variable_cache = VariableCache()


class Scope:

    def __init__(self):
        self.value = None
        self.set_scope(new_value='default')

    def set_scope(self, new_value: str):
        self.value = new_value
        variable_cache.store_variable(
            variable=Variable(
                name='std::scope',
                initial_value='{}'.format(copy.deepcopy(new_value))
            ),
            overwrite_existing=True
        )

    def __repr__(self)->str:
        return self.value

    def __str__(self)->str:
        return self.value


all_scoped_values = AllScopedValues()
scope = Scope()

