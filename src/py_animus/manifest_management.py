"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777`@`gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

import copy
import traceback
import hashlib
import json
import yaml
import importlib, os, inspect
import sys
import re
from py_animus import get_logger, get_utc_timestamp, is_debug_set_in_environment, parse_raw_yaml_data
import chardet


def get_modules_in_package(target_dir: str, logger=get_logger()):
    files = os.listdir(target_dir)
    sys.path.insert(0,target_dir)
    for file in files:
        if file not in ['__init__.py', '__pycache__']:
            if file[-3:] != '.py':
                continue    # pragma: no cover
            file_name = file[:-3]
            module_name = file_name
            for name, cls in inspect.getmembers(importlib.import_module(module_name), inspect.isclass):
                if cls.__module__ == module_name:
                    m = importlib.import_module(module_name)
                    clazz = getattr(m, name)
                    yield (clazz, name)


def dummy_manifest_lookup_function(name: str):  # pragma: no cover
    return


class ValuePlaceholder:

    def __init__(self, placeholder_name: str):
        self.placeholder_name = placeholder_name
        self.per_environment_values = dict()

    def add_environment_value(self, environment_name: str, value: object):
        if value is not None:
            if isinstance(value, str):
                value = value.replace('\n', '')
                value = value.replace('\r', '')
        self.per_environment_values[environment_name] = value

    def get_environment_value(self, environment_name: str, default_value_when_not_found: object=None, raise_exception_when_not_found: bool=True):
        if environment_name not in self.per_environment_values:
            if raise_exception_when_not_found is True:
                raise Exception('No value for environment "{}" for value placeholder "{}" found'.format(environment_name, self.placeholder_name))
            return default_value_when_not_found
        return copy.deepcopy(self.per_environment_values[environment_name])
    
    def to_dict(self):
        data = dict()
        data['name'] = self.placeholder_name
        data['environments'] = list()
        for env_name, env_val in self.per_environment_values.items():
            pev = dict()
            pev['environmentName'] = env_name
            pev['value'] = env_val
            data['environments'].append(copy.deepcopy(pev))
        return data


class ValuePlaceHolders:

    def __init__(self, logger=get_logger()):
        self.value_placeholder_names = dict()
        self.logger = logger

    def value_placeholder_exists(self, placeholder_name: str)->bool:
        if placeholder_name in self.value_placeholder_names:
            return True
        return False

    def get_value_placeholder(self, placeholder_name: str, create_in_not_exists: bool=True)->ValuePlaceholder:
        if self.value_placeholder_exists(placeholder_name=placeholder_name) is False and create_in_not_exists is True:
            return self.create_new_value_placeholder(placeholder_name=placeholder_name)
        elif self.value_placeholder_exists(placeholder_name=placeholder_name) is False and create_in_not_exists is False:
            raise Exception('ValuePlaceholder named "{}" not found'.format(placeholder_name))
        return copy.deepcopy(self.value_placeholder_names[placeholder_name])

    def create_new_value_placeholder(self, placeholder_name: str)->ValuePlaceholder:
        vp = ValuePlaceholder(placeholder_name=placeholder_name)
        self.value_placeholder_names[placeholder_name] = copy.deepcopy(vp)
        return copy.deepcopy(vp)
    
    def add_environment_value(self, placeholder_name: str, environment_name: str, value: object):
        vp = self.get_value_placeholder(placeholder_name=placeholder_name, create_in_not_exists=True)
        vp.add_environment_value(environment_name=environment_name, value=value)
        self.value_placeholder_names[placeholder_name] = copy.deepcopy(vp)

    def to_dict(self):
        data = dict()
        data['values'] = list()
        for vp_name in list(self.value_placeholder_names.keys()):
            vp = self.get_value_placeholder(placeholder_name=vp_name)
            data['values'].append(vp.to_dict())
        return data

    def parse_and_replace_placeholders_in_string(
            self,
            input_str: str,
            environment_name: str,
            default_value_when_not_found: object='',
            raise_exception_when_not_found: bool=False
        ):
        self.logger.debug('Parsing for placeholders. input_str="{}"'.format(input_str))
        return_str = copy.deepcopy(input_str)
        if input_str.find('{}{} .Values.'.format('{', '{')) >= 0:
            for matched_placeholder in re.findall('\{\{\s+\.Values\.([\w|\s|\-|\_|\.|\:]+)\s+\}\}', input_str):
                return_str = return_str.replace(
                    '{}{} .Values.{} {}{}'.format('{', '{', matched_placeholder, '}', '}'),
                    self.get_value_placeholder(
                        placeholder_name=matched_placeholder,
                        create_in_not_exists=True
                    ).get_environment_value(
                        environment_name=environment_name,
                        default_value_when_not_found=default_value_when_not_found,
                        raise_exception_when_not_found=raise_exception_when_not_found
                    )
                )
        self.logger.debug('   return_str="{}'.format(return_str))
        return return_str


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
        value: Any object containing a any value
        ttl: Integer with the time to live for the variable value in the cache (in seconds, default is -1 or unlimited lifespan while the application is running)
        init_timestamp: Integer with the UTC timestamp when the Variable was initiated or when the timer was reset when the value was updated
        debug: boolean value used mainly internally. Debug can be enabled with the environment variable DEBUG set to value of "1"
        logger: The logging.Logger class used for logging.
    """

    def __init__(self, name: str, initial_value=None, ttl: int=-1, logger=get_logger(), mask_in_logs: bool=False):
        """Initializes a new instance of a Variable to be stored in the VariableCache.

        Args:
          name: String with a unique name of this variable. (Will be validated as unique in VariableCache)
          initial_value: Object storing some initial value (Optional, default=None)
          ttl: Integer of seconds for Variable's value to be considered valid in the context of the VariableCache. (Optional, default=-1 which never expires)
          logger: An instance of logging.Logger used for logging (Optional, default is teh result from internal call to get_logger())
        """
        self.name = name
        self.value = initial_value
        self.ttl = ttl
        self.init_timestamp = get_utc_timestamp(with_decimal=False)
        self.debug = is_debug_set_in_environment()
        self.logger = logger
        self.mask_in_logs = mask_in_logs

    def _log_debug(self, message):
        if self.debug is True:
            self.logger.debug('[{}:{}] {}'.format(self.__class__.__name__, self.name, message))

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
        logger: The logging.Logger class used for logging.
    """

    def __init__(self, logger=get_logger()):
        """Initializes a new instance of a VariableCache hold a collection of Variable instances.

        Args:
          logger: An instance of logging.Logger used for logging (Optional, default is teh result from internal call to get_logger())
        """
        self.values = dict()
        self.logger = logger

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
            self.logger.debug('[variable_name={}] Variable NOT FOUND, and raise_exception_on_not_found is set to True'.format(variable_name))
            raise Exception('Variable "{}" not found'.format(variable_name))
        elif variable_name not in self.values and raise_exception_on_not_found is False:
            self.logger.debug('[variable_name={}] Variable NOT FOUND, and raise_exception_on_not_found is set to False - Returning default_value_if_not_found'.format(variable_name))
            return default_value_if_not_found
        return copy.deepcopy(self.values[variable_name].get_value(value_if_expired=value_if_expired, raise_exception_on_expired=raise_exception_on_expired, reset_timer_on_value_read=reset_timer_on_value_read, for_logging=for_logging))

    def delete_variable(self, variable_name: str):
        if variable_name in self.values:
            self.logger.debug('[variable_name={}] Deleted'.format(variable_name))
            self.values.pop(variable_name)

    def to_dict(self, for_logging: bool=False):
        data = dict()
        for k,v in self.values.items():
            v_dict = v.to_dict(for_logging=for_logging)
            data[k] = v_dict
        return data

    def __str__(self)->str:
        return json.dumps(self.to_dict(for_logging=True))


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

    def __init__(self, logger=get_logger(), post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
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
        self.logger = logger
        self.initialized = False
        self.post_parsing_method = post_parsing_method
        self.checksum = None
        self.dependency_processing_counter = dict()
        self.target_environments = ['default',]
        self.original_manifest = dict()

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
                self.logger.debug('[{}:{}:{}] {}'.format(self.kind, name, self.version, message))
        elif level.lower().startswith('i'):
            self.logger.info('[{}:{}:{}] {}'.format(self.kind, name, self.version, message))
        elif level.lower().startswith('w'):
            self.logger.warning('[{}:{}:{}] {}'.format(self.kind, name, self.version, message))
        elif level.lower().startswith('e'):
            self.logger.error('[{}:{}:{}] {}'.format(self.kind, name, self.version, message))

    def _decode_str_based_on_encoding(self, input_str)->str:
        try:
            encoding = chardet.detect(input_str)['encoding']
            return copy.deepcopy(input_str.decode(encoding))
        except:
            pass
        return input_str

    def _process_and_replace_variable_placeholders_in_string(self, input_str: str, variable_cache: VariableCache=VariableCache())->str:
        return_str = copy.deepcopy(input_str)
        if input_str.find('{}{} .Variables.'.format('{', '{')) >= 0:
            for matched_placeholder in re.findall('\{\{\s+\.Variables\.([\w|\s|\-|\_|\.|\:]+)\s+\}\}', input_str):
                return_str = return_str.replace(
                    '{}{} .Variables.{} {}{}'.format('{', '{', matched_placeholder, '}', '}'),
                    variable_cache.get_value(
                        variable_name=matched_placeholder,
                        value_if_expired='',
                        default_value_if_not_found='',
                        raise_exception_on_expired=False,
                        raise_exception_on_not_found=False,
                        for_logging=False
                    )
                )
        if return_str is None:
            return_str = ''
        elif isinstance(return_str, dict) or isinstance(return_str, list):
            return_str = copy.deepcopy(json.dumps(return_str))

        return_str = copy.deepcopy(self._decode_str_based_on_encoding(input_str=return_str))
        if not isinstance(return_str, str):
            return_str = copy.deepcopy(str(return_str))

        return return_str

    def _process_dict_for_value_placeholders(self, d: dict, value_placeholders: ValuePlaceHolders, environment_name: str, variable_cache: VariableCache=VariableCache())->dict:
        final_d = dict()
        for k,v in d.items():
            if isinstance(v, dict):
                final_d[k] = copy.deepcopy(self._process_dict_for_value_placeholders(d=v, value_placeholders=value_placeholders, environment_name=environment_name, variable_cache=variable_cache))
            elif isinstance(v, str):
                interim_str = copy.deepcopy(
                    value_placeholders.parse_and_replace_placeholders_in_string(
                        input_str=v,
                        environment_name=environment_name,
                        default_value_when_not_found=v,
                        raise_exception_when_not_found=False
                    )
                )
                final_d[k] = copy.deepcopy(
                    self._process_and_replace_variable_placeholders_in_string(
                        input_str=interim_str,
                        variable_cache=variable_cache
                    )
                )
            elif isinstance(v, list):
                temp_d = dict()
                parsed_list = list()
                counter = 0
                for item in v:
                    temp_d['part_{}'.format(counter)] = item
                    counter += 1
                parsed_temp_d = copy.deepcopy(self._process_dict_for_value_placeholders(d=temp_d, value_placeholders=value_placeholders, environment_name=environment_name, variable_cache=variable_cache))
                for temp_k, temp_v in parsed_temp_d.items():
                    parsed_list.append(temp_v)
                final_d[k] = copy.deepcopy(parsed_list)
            elif isinstance(v, int):
                final_d[k] = copy.deepcopy(v)
            else:
                final_d[k] = copy.deepcopy(v)
        return final_d

    def process_value_placeholders(self, value_placeholders: ValuePlaceHolders, environment_name: str, variable_cache: VariableCache=VariableCache()):
        manifest_data_with_parsed_value_placeholder_values = self._process_dict_for_value_placeholders(d=copy.deepcopy(self.original_manifest), value_placeholders=value_placeholders, environment_name=environment_name, variable_cache=variable_cache)
        self.log(message='manifest_data_with_parsed_value_placeholder_values={}'.format(manifest_data_with_parsed_value_placeholder_values), level='debug')
        self.metadata = copy.deepcopy(manifest_data_with_parsed_value_placeholder_values['metadata'])
        self.spec = copy.deepcopy(manifest_data_with_parsed_value_placeholder_values['spec'])

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

    def process_dependencies(
        self,
        action: str,
        process_dependency_if_already_applied: bool,
        process_dependency_if_not_already_applied: bool,
        manifest_lookup_function: object=dummy_manifest_lookup_function,
        variable_cache: VariableCache=VariableCache(),
        process_self_post_dependency_processing: bool=True,
        dependency_processing_rounds: dict=dict(),
        target_environment: str='default', 
        value_placeholders: ValuePlaceHolders=ValuePlaceHolders()
    ):
        """Called via the ManifestManager just before calling the `apply_manifest()` or `delete_manifest()`

        Looks at `metadata.dependencies.*` to determine which other manifests has to be processed before the main action for this manifest is processed

        Args:
          action: String with the appropriate command by which the lookup in `metadata.dependencies.*` will be done
          process_dependency_if_already_applied: bool, If set to True, will process dependencies again, even if it was previously processed (as determined by the implemented_manifest_differ_from_this_manifest() method)
          process_dependency_if_not_already_applied: bool, If set to true, process dependencies
          manifest_lookup_function: A function passed in by the ManifestManager. Called with `manifest_lookup_function(name='...')`. Implemented in ManifestManager.get_manifest_instance_by_name()
          variable_cache: A reference to the current instance of the VariableCache
          process_self_post_dependency_processing: bool=True, If set to True, run own apply/delete actions
          dependency_processing_rounds: dict that tracks how many times processing happened in order to limit endless processing loops.
          target_environment: string with the target environment
          value_placeholders: ValuePlaceHolders instance that contains the per environment placeholder values that will be passed on during processing in order for final field values to be determined.
        """
        if 'environments' in self.metadata:
            if target_environment not in self.metadata['environments']:
                return
        if 'dependencies' in self.metadata:

            if self.metadata['name'] not in dependency_processing_rounds:
                dependency_processing_rounds[self.metadata['name']] = 1
            else:
                dependency_processing_rounds[self.metadata['name']] += 1
            if dependency_processing_rounds[self.metadata['name']] > 2:
                self.log(message='dependency_processing_rounds for "{}" is now >2. Possible recursion detected. Throwing exception for safety reasons'.format(self.metadata['name']),level='error')
                raise Exception('Possible recursion detected')
            
            if action in self.metadata['dependencies']:
                for dependant_manifest_name in self.metadata['dependencies'][action]:
                    self.log(message='Processing dependency named "{}" for manifest "{}" while processing action "{}"'.format(dependant_manifest_name, self.metadata['name'], action), level='debug')
                    
                    dependency_manifest_implementation = manifest_lookup_function(name=dependant_manifest_name)
                    dependency_manifest_applied_previously = not dependency_manifest_implementation.implemented_manifest_differ_from_this_manifest(manifest_lookup_function=manifest_lookup_function, variable_cache=variable_cache, target_environment=target_environment, value_placeholders=value_placeholders)
                    self.log(
                        message='Dependency named "{}" previously applied: {}'.format(
                            dependency_manifest_implementation.metadata['name'],
                            dependency_manifest_applied_previously
                        ),
                        level='debug'
                    )
                    if dependency_manifest_applied_previously == process_dependency_if_already_applied:
                        self.log(message='Dependency named "{}" will be applied because process_dependency_if_already_applied is TRUE'.format(dependency_manifest_implementation.metadata['name']),level='debug')   
                        dependency_manifest_implementation.process_dependencies(
                            action=action,
                            manifest_lookup_function=manifest_lookup_function,
                            variable_cache=variable_cache,
                            process_self_post_dependency_processing=process_self_post_dependency_processing,
                            process_dependency_if_already_applied=process_dependency_if_already_applied,
                            process_dependency_if_not_already_applied=process_dependency_if_not_already_applied,
                            dependency_processing_rounds=dependency_processing_rounds,
                            target_environment=target_environment,
                            value_placeholders=value_placeholders
                        )
                    else:
                        self.log(message='Dependency named "{}" will NOT be applied because process_dependency_if_already_applied is FALSE'.format(dependency_manifest_implementation.metadata['name']),level='debug')   
                    if dependency_manifest_applied_previously == process_dependency_if_not_already_applied:
                        self.log(message='Dependency named "{}" will be applied because process_dependency_if_not_already_applied is TRUE'.format(dependency_manifest_implementation.metadata['name']),level='debug')   
                        dependency_manifest_implementation.process_dependencies(
                            action=action,
                            manifest_lookup_function=manifest_lookup_function,
                            variable_cache=variable_cache,
                            process_self_post_dependency_processing=process_self_post_dependency_processing,
                            process_dependency_if_already_applied=process_dependency_if_already_applied,
                            process_dependency_if_not_already_applied=process_dependency_if_not_already_applied,
                            dependency_processing_rounds=dependency_processing_rounds,
                            target_environment=target_environment,
                            value_placeholders=value_placeholders
                        )
                    else:
                        self.log(message='Dependency named "{}" will be applied because process_dependency_if_not_already_applied is FALSE'.format(dependency_manifest_implementation.metadata['name']),level='debug')   

            else:
                self.log(message='No dependencies for action "{}" for manifest "{}"'.format(action, self.metadata['name']), level='warning')
        else:
            self.log(message='No dependencies for manifest "{}" while processing action "{}"'.format(self.metadata['name'], action), level='debug')

        if process_self_post_dependency_processing is True:
            if action == 'apply':
                self.process_value_placeholders(value_placeholders=value_placeholders, environment_name=target_environment, variable_cache=variable_cache)
                self.apply_manifest(manifest_lookup_function=manifest_lookup_function, variable_cache=variable_cache, target_environment=target_environment, value_placeholders=value_placeholders)
            if action == 'delete':
                self.process_value_placeholders(value_placeholders=value_placeholders, environment_name=target_environment, variable_cache=variable_cache)
                self.delete_manifest(manifest_lookup_function=manifest_lookup_function, variable_cache=variable_cache, target_environment=target_environment, value_placeholders=value_placeholders)
        else:
            self.log(message='SELF was NOT YET PROCESSED for manifest "{}" while processing action "{}"'.format(self.metadata['name'], action), level='debug')

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

    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders())->bool:    # pragma: no cover
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
          variable_cache: A reference to the current instance of the VariableCache
          target_environment: string with the name of the target environment (default="default") (New since version 1.0.9)
          value_placeholders: ValuePlaceHolders instance containing all the per environment replacement values (New since version 1.0.9)

        Returns:
            Boolean True if the previous implementation is different from the current implementation

        Raises:
            Exception: When the method was not implemented by th user
            Exception: As determined by the user
        """
        raise Exception('To be implemented by user')

    def apply_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders()):  # pragma: no cover
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
          variable_cache: A reference to the current instance of the VariableCache
          increment_exec_counter: If set to true, the implementation should make the following call: `self.apply_execute_count += 1`
          target_environment: string with the name of the target environment (default="default") (New since version 1.0.9)
          value_placeholders: ValuePlaceHolders instance containing all the per environment replacement values (New since version 1.0.9)

        Returns:
            Any returned value will be ignored by the ManifestManager

        Raises:
            Exception: When the method was not implemented by th user
            Exception: As determined by the user
        """
        raise Exception('To be implemented by user')
    
    def delete_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders()):  # pragma: no cover
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
          variable_cache: A reference to the current instance of the VariableCache
          increment_exec_counter: If set to true, the implementation should make the following call: `self.delete_execute_count += 1`
          target_environment: string with the name of the target environment (default="default") (New since version 1.0.9)
          value_placeholders: ValuePlaceHolders instance containing all the per environment replacement values (New since version 1.0.9)

        Returns:
            Any returned value will be ignored by the ManifestManager

        Raises:
            Exception: When the method was not implemented by th user
            Exception: As determined by the user
        """
        raise Exception('To be implemented by user')


class VersionedClassRegister:

    def __init__(self, logger=get_logger()):
        self.classes = list()
        self.logger = logger
    
    def is_class_registered(self, kind: str, version: str=None)->bool:
        """Find a registered class of a certain kind, optionally matching the version as well
        
        Args:
          kind: String containing the class kind name
          version: String containing the class primary version (optional, ignored if not supplied)

        Returns:
            Boolean true if the registered class with kind name was found. If version was also supplied, return true if
            the kind name and primary version matches.
        """
        registered = False
        for registered_class in self.classes:
            if kind == registered_class.kind:
                if version is not None:
                    if version == registered_class.version:
                        return True
                else:
                    registered = True
        return registered
    
    def get_version_of_class(self, kind: str, version: str, _secondary_pass: bool=False)->ManifestBase:
        """Find a registered class of a certain kind, that support the supplied version
        
        Args:
          kind: String containing the class kind name
          version: String containing the version that must be supported

        Returns:
            If a class matching the kind that can process the required version is found a reference to it will be 
            returned.

        Raises:
            Exception: If no matching class supporting the requested version was found
        """
        current_identified_clazz = None
        supported_versions = dict()

        # Try and find a version of the class that is supported
        for registered_class in self.classes:
            if kind == registered_class.kind:
                if registered_class.version == version:
                    current_identified_clazz = registered_class
                    return registered_class
                for supported_version in registered_class.supported_versions:
                    if supported_version not in supported_versions:
                        supported_versions[supported_version] = list()
                    else:
                        supported_versions[supported_version].append(registered_class.version)

        # If we have not found a direct version match yet, look at the highest version of class that supports this version
        if _secondary_pass is False:
            if current_identified_clazz is None:
                if version in supported_versions:
                    potential_versions = copy.deepcopy(supported_versions[version])
                    if len(potential_versions) > 0:
                        potential_versions.sort(reverse=True)   # Rank from highest version to lowest
                        current_identified_clazz = self.get_version_of_class(kind=kind, version=potential_versions[0], _secondary_pass=True)

        # The result...
        if current_identified_clazz is None:
            raise Exception('No supported implementation of "{}" for version "{}" found'.format(kind, version))
        return current_identified_clazz

    def add_class(self, clazz: ManifestBase):
        if self.is_class_registered(kind=clazz.kind, version=clazz.version) is False:
            self.classes.append(clazz)
            self.logger.info(
                'Registered class kind "{}" version "{}" supporting also versions "{}" of manifests'.format(
                    clazz.kind,
                    clazz.version,
                    clazz.supported_versions
                )
            )
        else:
            self.logger.info('Class "{}" with version "{}" already registered - ignoring'.format(clazz.kind, clazz.version))

    def to_dict(self):
        result = dict()
        for clazz in self.classes:
            if clazz.kind not in result:
                result[clazz.kind] = dict()
                result[clazz.kind]['versions'] = list()
                result[clazz.kind]['versions'].append(clazz.version)
                for version in clazz.supported_versions:
                    if version not in result[clazz.kind]['versions']:
                        result[clazz.kind]['versions'].append(version)
                result[clazz.kind]['versions'].sort()
            else:
                if clazz.version not in result[clazz.kind]['versions']:
                    result[clazz.kind]['versions'].append(clazz.version)
                for version in clazz.supported_versions:
                    if version not in result[clazz.kind]['versions']:
                        result[clazz.kind]['versions'].append(version)
                result[clazz.kind]['versions'].sort()
        return result
    
    def __str__(self)->str:
        return json.dumps(self.to_dict())


class DependencyReference:

    def __init__(self, src: str, dst: str='NO-DEP', count: int=1):
        self.src = src
        self.dst = dst
        self.count = count

    def add_count(self):
        self.count += 1


class DependencyReferences:

    def __init__(self):
        self.dependencies = list()

    def exists(self, src: str, dst: str)->bool:
        for dr in self.dependencies:
            if dr.src == src and dr.dst == dst:
                return True
        return False

    def increment_counter(self, src: str, dst: str):
        updated_dependencies = list()
        for dr in self.dependencies:
            if dr.src == src and dr.dst == dst:
                dr.add_count()
            updated_dependencies.append(copy.deepcopy(dr))
        self.dependencies = updated_dependencies

    def add_dependency(self, src: str, dst: str):
        if self.exists(src=src, dst=dst) is True:
            self.increment_counter(src=src, dst=dst)
        else:
            self.dependencies.append(DependencyReference(src=src, dst=dst))

    def get_dependency_for_src(self, src: str)->list:
        deps = list()
        if src != 'NO-DEP':
            for dr in self.dependencies:
                if dr.src == src:
                    deps.append(dr.dst)
        return deps

    def direct_circular_references_detected(self)->bool:
        for dr in self.dependencies:
            dst_deps = self.get_dependency_for_src(src=dr.dst)
            if dr.src in dst_deps:
                return True
        return False


class ManifestManager:

    def __init__(
            self,
            variable_cache: VariableCache,
            logger=get_logger(),
            max_calls_to_manifest: int=int(os.getenv('MAX_CALLS_TO_MANIFEST', '10')),
            environments: list=['default',],
            values_files: list=['values.yaml',]
        ):
        self.versioned_class_register = VersionedClassRegister(logger=logger)
        self.manifest_instances = dict()
        self.manifest_data_by_manifest_name = dict()
        self.variable_cache = variable_cache
        self.logger = logger
        self.apply_drs = DependencyReferences()
        self.delete_drs = DependencyReferences()
        self.max_calls_to_manifest = max_calls_to_manifest
        self.executions_per_manifest_instance = dict()
        self.environments = environments
        self.environment_values = ValuePlaceHolders(logger=logger)
        self._load_values(files=values_files)
        self.logger.debug('LOADED environment_values: {}'.format(json.dumps(self.environment_values.to_dict())))

    def _load_values_from_file(self, file: str):
        try:
            self.logger.info('Attempting to load values from file "{}"'.format(file))
            with open(file, 'r') as f:
                configuration_data = parse_raw_yaml_data(yaml_data=f.read(), logger=self.logger)
            self.logger.debug('_load_values_from_file(): configuration_data={}'.format(configuration_data))
            for part, data in configuration_data.items():
                if 'values' in  data:
                    for value in data['values']:
                        if 'environments' in value:
                            environments = value['environments']
                            for environment_data in environments:
                                if 'environmentName' in environment_data and 'value' in environment_data:
                                    self.environment_values.add_environment_value(placeholder_name=value['name'], environment_name=environment_data['environmentName'], value=environment_data['value'])
            self.logger.info('   Loaded values from file "{}"'.format(file))
        except:
            self.logger.error('Failed to load values from file "{}"'.format(file))
            self.logger.error('EXCEPTION: {}'.format(traceback.format_exc()))

    def _load_values(self, files: list):
        try:
            for file in files:
                if isinstance(file, str):
                    self._load_values_from_file(file=file)
                elif isinstance(file, list):
                    self._load_values(file)
        except:
            self.logger.error('Failed to load values from files. files: {}'.format(files))
            self.logger.error('EXCEPTION: {}'.format(traceback.format_exc()))

    def register_manifest_class(self, manifest_base: ManifestBase):
        if isinstance(manifest_base, ManifestBase) is False:
            raise Exception('Incorrect Base Class')
        self.versioned_class_register.add_class(clazz=manifest_base)

    def load_manifest_class_definition_from_file(self, plugin_file_path: str):
        for returned_class, kind in get_modules_in_package(target_dir=plugin_file_path, logger=self.logger):
             self.register_manifest_class(manifest_base=returned_class(logger=self.logger))
        self.logger.info('Registered classes: {}'.format(str(self.versioned_class_register)))

    def get_manifest_instance_by_name(self, name: str)->ManifestBase:
        for key, manifest_instance in self.manifest_instances.items():
            if manifest_instance.metadata['name'] == name or '{}:{}:{}'.format(manifest_instance.metadata['name'],manifest_instance.version,manifest_instance.checksum) == name:
                return manifest_instance
        raise Exception('No manifest instance for "{}" found'.format(name))
    
    def _record_manifest_instance_call(self, name: str):
        if name in self.executions_per_manifest_instance:
            self.executions_per_manifest_instance[name] += 1
        else:
            self.executions_per_manifest_instance[name] = 1

    def _max_execution_count_reached(self, manifest_instance: ManifestBase)->bool:
        if manifest_instance.metadata['name'] in self.executions_per_manifest_instance:
            if self.executions_per_manifest_instance[manifest_instance.metadata['name']] >= self.max_calls_to_manifest:
                return True
        else:
            self.executions_per_manifest_instance[manifest_instance.metadata['name']] = 0
        return False
    
    def _can_execute_again(self, manifest_instance: ManifestBase)->bool:
        return not self._max_execution_count_reached(manifest_instance=manifest_instance)

    def apply_manifest(self, name: str, skip_dependency_processing: bool=False, target_environment: str='default'):
        manifest_instance = self.get_manifest_instance_by_name(name=name)
        self.logger.info('Checking if environment "{}" ({}) is in manifest_instance target environments "{}" ({})'.format(target_environment, type(target_environment), manifest_instance.metadata['environments'], type(manifest_instance.target_environments)))
        if target_environment not in manifest_instance.metadata['environments']:
            return
        self.logger.debug('ManifestManager.apply_manifest(): manifest_instance named "{}" loaded. Target environment set to "{}"'.format(manifest_instance.metadata['name'], target_environment))

        do_apply_in_environment = False
        for te in self.environments:
            self.logger.debug('* EVAL: te="{}" == target_environment="{}"'.format(te, target_environment))
            if te == target_environment:
                if te in manifest_instance.metadata['environments']:
                    self.logger.info('ManifestManager.apply_manifest(): manifest_instance named "{}" targeted for environment "{}"'.format(manifest_instance.metadata['name'], te))    
                    do_apply_in_environment = True
        if do_apply_in_environment is False:
            self.logger.warning('ManifestManager.apply_manifest(): manifest_instance named "{}" loaded not selected for target environment "{}". Skipping.'.format(manifest_instance.metadata['name'], target_environment))
            return

        if 'skipApplyAll' in manifest_instance.metadata:
            if manifest_instance.metadata['skipApplyAll'] is True:
                self.logger.warning('ManifestManager:apply_manifest(): Manifest named "{}" skipped because of skipApplyAll setting'.format(manifest_instance.metadata['name']))
                return

        if skip_dependency_processing is True:
            manifest_instance.process_value_placeholders(value_placeholders=self.environment_values, environment_name=target_environment, variable_cache=self.variable_cache)
            manifest_instance.apply_manifest(manifest_lookup_function=self.get_manifest_instance_by_name, variable_cache=self.variable_cache, target_environment=target_environment, value_placeholders=self.environment_values)
            return
        
        if 'executeOnlyOnceOnApply' in manifest_instance.metadata:
            if manifest_instance.metadata['executeOnlyOnceOnApply'] is True and self.executions_per_manifest_instance[manifest_instance.metadata['name']] > 0:
                self.logger.warning('ManifestManager:apply_manifest(): Manifest named "{}" skipped because executeOnlyOnceOnApply is TRUE and it was already executed before'.format(manifest_instance.metadata['name']))
                return

        self._record_manifest_instance_call(name=manifest_instance.metadata['name'])
        self.logger.debug('ManifestManager.apply_manifest(): Previous exec count: {}'.format(self.executions_per_manifest_instance[manifest_instance.metadata['name']]))
            
        if self._can_execute_again(manifest_instance=manifest_instance) is False:
            raise Exception('ManifestManager.apply_manifest(): Maximum executions reached when attempting to process manifest named "{}"'.format(manifest_instance.metadata['name']))

        manifest_instance.process_dependencies(
            action='apply',
            process_dependency_if_already_applied=False,
            process_dependency_if_not_already_applied=True,
            manifest_lookup_function=self.get_manifest_instance_by_name,
            variable_cache=self.variable_cache,
            process_self_post_dependency_processing=True,
            target_environment=target_environment,
            value_placeholders=self.environment_values
        )

    def delete_manifest(self, name: str, skip_dependency_processing: bool=False, target_environment: str='default'):
        manifest_instance = self.get_manifest_instance_by_name(name=name)
        if target_environment not in manifest_instance.metadata['environments']:
            return
        self.logger.debug('ManifestManager.delete_manifest(): manifest_instance named "{}" loaded.. Target environment set to "{}"'.format(manifest_instance.metadata['name'], target_environment))

        do_delete_in_environment = False
        for te in self.environments:
            self.logger.debug('* EVAL: te="{}" == target_environment="{}"'.format(te, target_environment))
            if te == target_environment:
                if te in manifest_instance.metadata['environments']:
                    self.logger.info('ManifestManager.delete_manifest(): manifest_instance named "{}" targeted for environment "{}"'.format(manifest_instance.metadata['name'], te))    
                    do_delete_in_environment = True
        if do_delete_in_environment is False:
            self.logger.warning('ManifestManager.delete_manifest(): manifest_instance named "{}" loaded not selected for target environment "{}". Skipping.'.format(manifest_instance.metadata['name'], target_environment))
            return

        if 'skipDeleteAll' in manifest_instance.metadata:
            if manifest_instance.metadata['skipDeleteAll'] is True:
                self.logger.warning('ManifestManager:delete_manifest(): Manifest named "{}" skipped because of skipDeleteAll setting'.format(manifest_instance.metadata['name']))
                return

        if skip_dependency_processing is True:
            manifest_instance.process_value_placeholders(value_placeholders=self.environment_values, environment_name=target_environment, variable_cache=self.variable_cache)
            manifest_instance.delete_manifest(manifest_lookup_function=self.get_manifest_instance_by_name, variable_cache=self.variable_cache, target_environment=target_environment, value_placeholders=self.environment_values)
            return
        
        if 'executeOnlyOnceOnDelete' in manifest_instance.metadata:
            if manifest_instance.metadata['executeOnlyOnceOnDelete'] is True and self.executions_per_manifest_instance[manifest_instance.metadata['name']] > 0:
                self.logger.warning('ManifestManager:delete_manifest(): Manifest named "{}" skipped because executeOnlyOnceOnDelete is TRUE and it was already executed before'.format(manifest_instance.metadata['name']))
                return
        
        self._record_manifest_instance_call(name=manifest_instance.metadata['name'])
        self.logger.debug('ManifestManager.delete_manifest(): Previous exec count: {}'.format(self.executions_per_manifest_instance[manifest_instance.metadata['name']]))
            
        if self._can_execute_again(manifest_instance=manifest_instance) is False:
            raise Exception('ManifestManager.delete_manifest(): Maximum executions reached when attempting to process manifest named "{}"'.format(manifest_instance.metadata['name']))
        
        manifest_instance.process_dependencies(
            action='delete',
            process_dependency_if_already_applied=True,
            process_dependency_if_not_already_applied=False,
            manifest_lookup_function=self.get_manifest_instance_by_name,
            variable_cache=self.variable_cache,
            process_self_post_dependency_processing=True,
            target_environment=target_environment,
            value_placeholders=self.environment_values
        )

    def get_manifest_class_by_kind(self, kind: str, version: str=None):
        if version is None:
            raise Exception('Version is required')
        return self.versioned_class_register.get_version_of_class(kind=kind, version=version)
    
    def parse_manifest(self, manifest_data: dict):
        manifest_data = dict((k.lower(), v) for k,v in manifest_data.items())   # Convert first level keys to lower case
        version = None
        if 'version' in manifest_data:
            version = manifest_data['version']
        class_instance_copy = copy.deepcopy(self.get_manifest_class_by_kind(kind=manifest_data['kind'], version=version))
        if 'environments' not in manifest_data['metadata']:
            manifest_data['metadata']['environments'] = ['default',]

        class_instance_copy.parse_manifest(manifest_data=manifest_data, target_environments=self.environments)
        idx = '{}:{}:{}'.format(
            class_instance_copy.metadata['name'],
            class_instance_copy.version,
            class_instance_copy.checksum
        )

        if class_instance_copy.metadata['name'] not in self.executions_per_manifest_instance:
            self.executions_per_manifest_instance[class_instance_copy.metadata['name']] = 0

        # Dependency Circular Reference Detection
        self.logger.debug('ManifestManager:parse_manifest(): Direct Dependency Circular Reference Detection for manifest named "{}"'.format(class_instance_copy.metadata['name']))
        if 'dependencies' in class_instance_copy.metadata:
            if 'apply' in class_instance_copy.metadata['dependencies']:
                for dst in class_instance_copy.metadata['dependencies']['apply']:
                    self.logger.debug('ManifestManager:parse_manifest():    For manifest named "{}" storing apply dependency to manifest named "{}"'.format(class_instance_copy.metadata['name'], dst))
                    self.apply_drs.add_dependency(src=class_instance_copy.metadata['name'], dst=dst)
            if self.apply_drs.direct_circular_references_detected() is True:
                raise Exception('Direct dependency violation detected in class "{}" when parsing manifest named "{}" (apply section)'.format(class_instance_copy.kind, class_instance_copy.metadata['name']))
            if 'delete' in class_instance_copy.metadata['dependencies']:
                for dst in class_instance_copy.metadata['dependencies']['delete']:
                    self.logger.debug('ManifestManager:parse_manifest():    For manifest named "{}" storing delete dependency to manifest named "{}"'.format(class_instance_copy.metadata['name'], dst))
                    self.delete_drs.add_dependency(src=class_instance_copy.metadata['name'], dst=dst)
            if self.delete_drs.direct_circular_references_detected() is True:
                raise Exception('Direct dependency violation detected in class "{}" when parsing manifest named "{}" (delete section)'.format(class_instance_copy.kind, class_instance_copy.metadata['name']))
        self.logger.info('ManifestManager:parse_manifest(): NO direct dependency circular reference detected for manifest named "{}"'.format(class_instance_copy.metadata['name']))

        self.logger.info('ManifestManager:parse_manifest(): Stored parsed manifest instance "{}"'.format(idx))
        self.manifest_instances[idx] = class_instance_copy
        self.manifest_data_by_manifest_name[manifest_data['metadata']['name']] = manifest_data

