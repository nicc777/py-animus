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
import hashlib
import yaml
from py_animus.helpers import get_utc_timestamp, is_debug_set_in_environment


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
    DELETE_PENDING              = 'APPLY_PENDING'
    DELETE_DONE                 = 'APPLY_DONE'
    DELETE_ABORTED_WITH_ERRORS  = 'APPLY_ABORTED_WITH_ERRORS'
    DELETE_DELETE_EXISTING      = 'APPLY_DELETE_EXISTING'
    DELETE_SKIP                 = 'APPLY_SKIP'
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
        'APPLY_PENDING',
        'APPLY_DONE',
        'APPLY_ABORTED_WITH_ERRORS',
        'APPLY_DELETE_EXISTING',
        'APPLY_SKIP',
    )

    def __init__(self, kind: str, name: str, action_name: str, action_status: str):
        if action_status not in self._possible_actions:
            raise Exception('Unsupported Action Status "{}"'.format(action_status))
        self.current_status = action_status
        self.kind = kind
        self.name = name
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

    def __init__(self):
        self.actions = dict()
        self.progress = 0.0

    def _update_progress(self):
        if len(self.actions) > 0:
            done_count = 0
            for action in self.actions:
                for complete_action in self._actions_considered_completed:
                    if complete_action == action.current_status:
                        done_count += 1
            self.progress = done_count / len(self.actions)
        else:
            self.progress = 0.0

    def add_or_update_action(self, action: Action):
        idx = '{}:{}'.format(action.kind, action.name)
        self.actions[idx] = action
        self._update_progress()

    def get_action_names(self, kind: str, name: str)->tuple:
        action_names = list()
        for key in list(self.actions.keys()):
            a_kind, a_name, a_action_name = key.split(':')
            if a_kind == kind and a_name == name:
                action_names.append(a_action_name)
        return tuple(action_names)
    
    def get_action_values_for_manifest(self, kind: str, name: str)->list:
        found_actions = list()
        for key in self.get_action_names(kind=kind, name=name):
            a_kind, a_name, _a_action_name = key.split(':')
            found_actions.append(self.get_action_status(kind=a_kind, name=a_name, action_name=_a_action_name))
        return found_actions

    def get_action_status(self, kind: str, name: str, action_name: str)->str:
        idx = '{}:{}:{}'.format(kind, name, action_name)
        if idx not in self.actions:
            raise Exception('No action status found for kind "{}" named "{}" for action name "{}"').format(kind, name, action_name)
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
            init_with_default_value_if_not_found: bool=False,
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
        if variable_name not in self.values and init_with_default_value_if_not_found is True:
            self.store_variable(
                variable=Variable(
                    name=variable_name,
                    initial_value=default_value_if_not_found
                )
            )
        if variable_name not in self.values and raise_exception_on_not_found is True:
            logging.debug('[variable_name={}] Variable NOT FOUND, and raise_exception_on_not_found is set to True'.format(variable_name))
            raise Exception('Variable "{}" not found'.format(variable_name))
        elif variable_name not in self.values and raise_exception_on_not_found is False:
            logging.debug('[variable_name={}] Variable NOT FOUND, and raise_exception_on_not_found is set to False - Returning default_value_if_not_found'.format(variable_name))
            return default_value_if_not_found
        return copy.deepcopy(self.values[variable_name].get_value(value_if_expired=value_if_expired, raise_exception_on_expired=raise_exception_on_expired, reset_timer_on_value_read=reset_timer_on_value_read, for_logging=for_logging))

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
    


class Scope:

    def __init__(self):
        self.value = 'default'

    def set_scope(self, new_value: str):
        self.value = new_value

    def __repr__(self)->str:
        return self.value

    def __str__(self)->str:
        return self.value


all_scoped_values = AllScopedValues()
variable_cache = VariableCache()
scope = Scope()


class ManifestBase:
    """ManifestBase needs to be extended by a user to implement a class that can handle the implementation logic of 
    applying a manifest during runtime.

    Any manifest will contain at least the following high level properties:

    * Version
    * Kind
    * Metadata
    * Spec

    The `Kind` name is used to match this class implementation of this ManifestBase class

    The Metadata must include at least a `name` property. This will assist other implementations to refer to this
    manifest.

    Example manifest:

    ```yaml
    kind: MyManifest1
    metadata:
        name: test1
    spec:
        val: 1
        more:
        - one
        - two
        - three
    ```

    Implementation of something to handle the above manifest:

    ```python
    class MyManifest1(ManifestBase):

        def __init__(
            self, 
            logger=get_logger(), 
            post_parsing_method: object = my_post_parsing_method, 
            version: str='v0.1', 
            supported_versions: tuple=('v0.1,')
        ):
            super().__init__(
                logger=logger, 
                post_parsing_method=post_parsing_method, 
                version=version, 
                supported_versions=supported_versions
            )

        def implemented_manifest_differ_from_this_manifest(
            self, 
            manifest_lookup_function: object=dummy_manifest_lookup_function
        )->bool:
            return True # We are always different

        def apply_manifest(
            self, 
            manifest_lookup_function: object=dummy_manifest_lookup_function, 
            variable_cache: VariableCache=VariableCache()
        ):
            variable_cache.store_variable(variable=Variable(name='{}:{}'.format(self.kind, self.metadata['name']), initial_value='Some Result Worth Saving'))
            return  # Assume some implementation
    ```

    When you implement operational logic, you can use the provided logger using the class `self.log()` method.

    The user is expected to implement the logic for the following methods:

    * `implemented_manifest_differ_from_this_manifest()` - Used to calculate at runtime if some prior execution of this class has changed, as compared to the checksum of the manifest.
    * `apply_manifest()` - After the manifest has been parsed and the `initialized` property is set to True, the user can implement the logic to apply the manifest to some real world scenario.

    Attributes:
        spec: Dictionary containing the parsed `spec` from a YAML manifest
        kind: The String value of the class implementation name
        metadata: Dictionary containing metadata
        version: String containing a version string (completely free form)
        supported_versions: A tuple of strings containing additional versions that this instance of the class can process
        debug: boolean value used mainly internally. Debug can be enabled with the environment variable DEBUG set to value of "1"
        logger: The logging.Logger class used for logging.
        initialized: A boolean that will be set to True once a manifest has been parsed and the values for this instance has been set
        post_parsing_method: Any custom method the user can provide that will be called after parsing (right after the `initialized` boolean is set to True)
        checksum: A calculated checksum of the parsed manifest. Can be used in the implementation of the `implemented_manifest_differ_from_this_manifest()` method to determine if some prior execution is different from the current manifest
    """

    def __init__(self, post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        """Initializes a new instance of a class extending ManifestBase 

        Args:
          logger: An instance of logging.Logger used for logging (Optional, default is teh result from internal call to get_logger())
          post_parsing_method: A Python function with the parameter signature `(**params)`. If set, this function will be called after parsing the manifest. (Optional, Default=None)
          version: A String containing the version of this implementation (Optional, Default='v1')
          supported_versions: A tuple of Strings containing all supported versions. (Optional, Default=('v1',))
        """
        self.spec = None
        self.kind = self.__class__.__name__
        self.metadata = dict()
        self.version = version
        self.ingested_manifest_version = None
        self.supported_versions = supported_versions
        self.debug = is_debug_set_in_environment()
        self.initialized = False
        self.post_parsing_method = post_parsing_method
        self.checksum = None
        self.target_environments = ['default',]
        self.original_manifest = dict()
        self.pending_action_description = 'No pending actions'

    def register_action(self, action_name: str, initial_status: str=Action.UNKNOWN):
        """
        This should be called during the determine_Actions() method processing

        Args:
          action_name: A String with a name for a action, for example "Create Some File"
          initial_status: String with the initial status as defined in the Action class
        """
        actions.add_or_update_action(action=Action(kind=self.kind, name=self.metadata['name'], action_name=action_name, action_status=initial_status))

    def log(self, message: str, level: str='info'): # pragma: no cover
        """During implementation, calls to `self.log()` can be made to log messages using the configure logger.

        The log level is supplied as an argument, with the default level being 'info'

        Args:
          message: A String with the message to log
          level: The log level, expressed as a string. One of `info`, `error`, `debug` or `warning`
        """
        name = 'not-yet-known'
        if 'name' in self.metadata:
            name = self.metadata['name']
        if level.lower().startswith('d'):
            if self.debug:
                logging.debug('[{}:{}:{}] {}'.format(self.kind, name, self.version, message))
        elif level.lower().startswith('i'):
            logging.info('[{}:{}:{}] {}'.format(self.kind, name, self.version, message))
        elif level.lower().startswith('w'):
            logging.warning('[{}:{}:{}] {}'.format(self.kind, name, self.version, message))
        elif level.lower().startswith('e'):
            logging.error('[{}:{}:{}] {}'.format(self.kind, name, self.version, message))

    def parse_manifest(self, manifest_data: dict, target_environments: list=['default',]):
        """Called via the ManifestManager when manifests files are parsed and one is found to belong to a class of this implementation.

        The user does not have to override this implementation.

        Args:
          manifest_data: A Dictionary of data from teh parsed Manifest file
        """
        self.target_environments = target_environments
        self.original_manifest = copy.deepcopy(manifest_data)
        converted_data = dict((k.lower(),v) for k,v in manifest_data.items()) # Convert keys to lowercase
        if 'kind' in converted_data:
            if converted_data['kind'] != self.kind:
                self.log(message='Kind mismatch. Got "{}" and expected "{}"'.format(converted_data['kind'], self.kind), level='error')
                return
        else:
            self.log(message='Kind property not present in data. Data={}'.format(manifest_data), level='error')
            raise Exception('Kind property not present in data.')
        if 'version' in converted_data:
            supported_version_found = False
            if converted_data['version'] in self.supported_versions:
                supported_version_found = True
                self.log(message='Manifest version "{}" found in class supported versions'.format(converted_data['version']), level='info')
            elif converted_data['version'] == self.version:
                supported_version_found = True
                self.log(message='Manifest version "{}" found in class main versions'.format(converted_data['version']), level='info')
            if supported_version_found is False:
                self.log(message='Version {} not supported by this implementation. Supported versions: {}'.format(converted_data['version'], self.supported_versions), level='error')
                raise Exception('Version {} not supported by this implementation.'.format(converted_data['version']))
            self.ingested_manifest_version = converted_data['version']
        else:
            self.log(message='Version property not present in data. Data={}'.format(manifest_data), level='error')
            raise Exception('Version property not present in data.')
        if 'metadata' in converted_data:
            if isinstance(converted_data['metadata'], dict):
                self.metadata = converted_data['metadata']
        if 'name' not in self.metadata:
            self.metadata['name'] = self.kind
            self.log(message='MetaData not supplied - using class Kind as name', level='warning')
        if 'spec' in converted_data:
            if isinstance(converted_data['spec'], dict) or isinstance(converted_data['spec'], list) or isinstance(converted_data['spec'], tuple):
                self.spec = converted_data['spec']
        self.initialized = True
        if self.post_parsing_method is not None:
            try:
                self.post_parsing_method(**self.__dict__)
            except:
                self.log(message='post_parsing_method failed with EXCEPTION: {}'.format(traceback.format_exc()), level='error')

        final_spec = dict()
        SUPPORTED_TYPES = (
            str,
            int,
            float,
            list,
            dict
        )
        for key, value in self.spec.items():
            final_spec[key] = copy.deepcopy(value)
            if value is not None:
                supported_type_found = False
                for supported_type in SUPPORTED_TYPES:
                    if isinstance(value, supported_type):
                        supported_type_found = True
                if supported_type_found is False:
                    final_spec[key] = copy.deepcopy(str(value))
        self.spec = copy.deepcopy(final_spec)
        converted_data['spec'] = copy.deepcopy(final_spec)

        self.checksum = hashlib.sha256(json.dumps(converted_data, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest() # Credit to https://stackoverflow.com/users/2082964/chris-maes for his hint on https://stackoverflow.com/questions/6923780/python-checksum-of-a-dict
        self.log(
            message='\n\nPOST PARSING. Manifest kind "{}" named "{}":\n   metadata: {}\n   spec: {}\n\n'.format(
                self.kind,
                self.metadata['name'],
                json.dumps(self.metadata),
                json.dumps(self.spec)
            ),
            level='debug'
        )

    def to_dict(self):
        """When the user or some other part of the systems required the data as a Dict, for example when to produce a
        YAML file.

        Returns:
            A dictionary of the Manifest data.
        """
        if self.initialized is False:
            raise Exception('Class not yet fully initialized')
        data = dict()
        data['kind'] = self.kind
        data['metadata'] = self.metadata
        data['version'] = self.version
        if self.spec is not None:
            data['spec'] = self.spec
        return data

    def __str__(self):
        """Produces a YAML representation of the class attributes

        Returns:
            A String in YAML format
        """
        return yaml.dump(self.to_dict())

    def implemented_manifest_differ_from_this_manifest(self, target_environment: str='default')->bool:    # pragma: no cover
        """A helper method to determine if the current manifest is different from a potentially previously implemented
        version

        The exact logic to derive the checksum of any previous implementation is left to the user. Ideally, calls
        should be made to determine some prior implementation that can reconstruct the original manifest from where the
        checksum can be calculated and compared to the current checksum.

        Example logic: 

        ```python
        // Retrieve some data about a prior implementation
        previous_implementation_data = dict()
        previous_implementation_data['kind'] = self.__class__.__name__
        previous_implementation_data['version'] = self.version // or some other version, if relevant...
        previous_implementation_data['metadata'] = self.metadata // or some other values, if relevant to determine difference...
        previous_implementation_data['spec'] = dict()
        // add data to previous_implementation_data['spec'] from a prior implementation as required
        if  hashlib.sha256(json.dumps(previous_implementation_data, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest() != self.checksum:
            return True
        return False
        ```

        **IMPORTANT** It is up to the implementation to parse the per target placeholder values. Consider the following example:

        ```python
        # Assuming we have a spec field called "name" (self.spec['name']), we can ensure the final value is set with:
        final_name = value_placeholders.parse_and_replace_placeholders_in_string(
            input_str=self.spec['name'],
            environment_name=target_environment,
            default_value_when_not_found='what_ever_is_appropriate'
        )
        ```

        Args:
          manifest_lookup_function: A function passed in by the ManifestManager. Called with `manifest_lookup_function(name='...')`. Implemented in ManifestManager.get_manifest_instance_by_name()
          target_environment: string with the name of the target environment (default="default") (New since version 1.0.9)

        Returns:
            Boolean True if the previous implementation is different from the current implementation

        Raises:
            Exception: When the method was not implemented by th user
            Exception: As determined by the user
        """
        raise Exception('To be implemented by user')

    def determine_actions(self, target_environment: str='default'):
        """
        TODO 
        """
        raise Exception('To be implemented by user')

    def apply_manifest(self, target_environment: str='default'):  # pragma: no cover
        """A  method to Implement the state as defined in a manifest.

        The ManifestManager will typically call this method to apply the manifest. The ManifestManager will NOT make a
        prior call to implemented_manifest_differ_from_this_manifest() and it is up to the user implementation of this
        method to determine if prior changes need to be taken into consideration. A common pattern during
        implementation is therefore:

        ```python
        if self.implemented_manifest_differ_from_this_manifest() is False:
            self.log(message='No changes from previous implementation detected')
            return
        // Proceed with the implementation here...
        ```

        Any results produced can be stored in the VariableCache as one or more Variable instances, for example:

        ```python
        // Some result is stored in the variable "result"
        variable_cache.store_variable(variable=Variable(name='some_name', initial_value=result), overwrite_existing=True)
        ```

        If this manifest relies on some other manifest, the `dummy_manifest_lookup_function()` function can be called
        to implement that manifest and get the result from the VariableCache, for example:

        ```python
        // Assuming we define our parent/dependency in the manifest as "spec.parent"
        parent_manifest = manifest_lookup_function(name=self.spec['parent'])    // Get an instance of ManifestBase implementation with teh provided name
        parent_manifest.apply_manifest(variable_cache=variable_cache)           // Ensure it is applied
        // Consume output from parent_manifest as stored in the variable_cache as needed...
        ```

        **IMPORTANT** It is up to the implementation to parse the per target placeholder values. Consider the following example:

        ```python
        # Assuming we have a spec field called "name" (self.spec['name']), we can ensure the final value is set with:
        final_name = value_placeholders.parse_and_replace_placeholders_in_string(
            input_str=self.spec['name'],
            environment_name=target_environment,
            default_value_when_not_found='what_ever_is_appropriate'
        )
        ```

        Args:
          manifest_lookup_function: A function passed in by the ManifestManager. Called with `manifest_lookup_function(name='...')`. Implemented in ManifestManager.get_manifest_instance_by_name()
          target_environment: string with the name of the target environment (default="default") (New since version 1.0.9)

        Returns:
            Any returned value will be ignored by the ManifestManager

        Raises:
            Exception: When the method was not implemented by th user
            Exception: As determined by the user
        """
        raise Exception('To be implemented by user')
    
    def delete_manifest(self, target_environment: str='default'):  # pragma: no cover
        """A  method to DELETE the current state as defined in a manifest.

        The ManifestManager will typically call this method to delete the manifest. The ManifestManager will NOT make a
        prior call to implemented_manifest_differ_from_this_manifest() and it is up to the user implementation of this
        method to determine if prior changes need to be taken into consideration. A common pattern during
        implementation is therefore:

        ```python
        if self.implemented_manifest_differ_from_this_manifest() is False:
            self.log(message='No changes from previous implementation detected')
            return
        // Proceed with the implementation here...
        ```

        Any results produced can be stored in the VariableCache as one or more Variable instances, for example:

        ```python
        // Some result is stored in the variable "result"
        variable_cache.store_variable(variable=Variable(name='some_name', initial_value=result), overwrite_existing=True)
        ```

        If this manifest relies on some other manifest, the `dummy_manifest_lookup_function()` function can be called
        to implement that manifest and get the result from the VariableCache, for example:

        ```python
        // Assuming we define our parent/dependency in the manifest as "spec.parent"
        parent_manifest = manifest_lookup_function(name=self.spec['parent'])    // Get an instance of ManifestBase implementation with teh provided name
        parent_manifest.apply_manifest(variable_cache=variable_cache)           // Ensure it is applied (or deleted, as required in this specific context)
        // Consume output from parent_manifest as stored in the variable_cache as needed...
        ```

        **IMPORTANT** It is up to the implementation to parse the per target placeholder values. Consider the following example:

        ```python
        # Assuming we have a spec field called "name" (self.spec['name']), we can ensure the final value is set with:
        final_name = value_placeholders.parse_and_replace_placeholders_in_string(
            input_str=self.spec['name'],
            environment_name=target_environment,
            default_value_when_not_found='what_ever_is_appropriate'
        )
        ```

        Args:
          manifest_lookup_function: A function passed in by the ManifestManager. Called with `manifest_lookup_function(name='...')`. Implemented in ManifestManager.get_manifest_instance_by_name()
          target_environment: string with the name of the target environment (default="default") (New since version 1.0.9)

        Returns:
            Any returned value will be ignored by the ManifestManager

        Raises:
            Exception: When the method was not implemented by th user
            Exception: As determined by the user
        """
        raise Exception('To be implemented by user')

