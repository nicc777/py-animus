"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

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
from py_animus import get_logger, get_utc_timestamp, is_debug_set_in_environment


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

    def __init__(self, name: str, initial_value=None, ttl: int=-1, logger=get_logger()):
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

    def get_value(self, value_if_expired=None, raise_exception_on_expired: bool=True, reset_timer_on_value_read: bool=False):
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
    
    def to_dict(self):
        data = {
            'ttl': self.ttl,
            'value': '{}'.format(str(self.value)),
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
            default_value_if_not_found=None
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
        return copy.deepcopy(self.values[variable_name].get_value(value_if_expired=value_if_expired, raise_exception_on_expired=raise_exception_on_expired, reset_timer_on_value_read=reset_timer_on_value_read))

    def to_dict(self):
        data = dict()
        for k,v in self.values.items():
            v_dict = v.to_dict()
            data[k] = v_dict
        return data

    def __str__(self)->str:
        return json.dumps(self.to_dict())


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

    def log(self, message: str, level: str='info'): # pragma: no cover
        """During implementation, calls to `self.log()` can be made to log messages using the configure logger.

        The log level is supplied as an argument, with the default level being 'info'

        Args:
          message: A String with the message to log
          level: The log level, expressed as a string. One of `info`, `error`, `debug` or `warning`
        """
        if level.lower().startswith('d'):
            if self.debug:
                self.logger.debug('[{}] {}'.format(self.kind, message))
        elif level.lower().startswith('i'):
            self.logger.info('[{}] {}'.format(self.kind, message))
        elif level.lower().startswith('w'):
            self.logger.warning('[{}] {}'.format(self.kind, message))
        elif level.lower().startswith('e'):
            self.logger.error('[{}] {}'.format(self.kind, message))

    def parse_manifest(self, manifest_data: dict):
        """Called via the ManifestManager when manifests files are parsed and one is found to belong to a class of this implementation.

        The user does not have to override this implementation.

        Args:
          manifest_data: A Dictionary of data from teh parsed Manifest file
        """
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

    def process_dependencies(self, action: str, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache()):
        """Called via the ManifestManager just before calling the `apply_manifest()` or `delete_manifest()`

        Looks at `metadata.dependencies.*` to determine which other manifests has to be processed before the main action for this manifest is processed

        Args:
          action: String with the appropriate command by which the lookup in `metadata.dependencies.*` will be done
          manifest_lookup_function: A function passed in by the ManifestManager. Called with `manifest_lookup_function(name='...')`. Implemented in ManifestManager.get_manifest_instance_by_name()
          variable_cache: A reference to the current instance of the VariableCache
        """
        if 'dependencies' in self.metadata:
            if action in self.metadata['dependencies']:
                for dependant_manifest_name in self.metadata['dependencies'][action]:
                    manifest_implementation = manifest_lookup_function(name=dependant_manifest_name)
                    if action == 'apply':
                        manifest_applied_previously = not manifest_implementation.implemented_manifest_differ_from_this_manifest(manifest_lookup_function=self.get_manifest_instance_by_name, variable_cache=self.variable_cache)
                        if manifest_applied_previously is False:
                            manifest_implementation.apply_manifest(manifest_lookup_function=self.get_manifest_instance_by_name, variable_cache=self.variable_cache)
                    if action == 'delete':
                        manifest_applied_previously = not manifest_implementation.implemented_manifest_differ_from_this_manifest(manifest_lookup_function=self.get_manifest_instance_by_name, variable_cache=self.variable_cache)
                        if manifest_applied_previously is True:
                            manifest_implementation.apply_manifest(manifest_lookup_function=self.get_manifest_instance_by_name, variable_cache=self.variable_cache)

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

    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache())->bool:    # pragma: no cover
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

        Args:
          manifest_lookup_function: A function passed in by the ManifestManager. Called with `manifest_lookup_function(name='...')`. Implemented in ManifestManager.get_manifest_instance_by_name()
          variable_cache: A reference to the current instance of the VariableCache

        Returns:
            Boolean True if the previous implementation checksum is different from the current manifest checksum.

        Raises:
            Exception: When the method was not implemented by th user
            Exception: As determined by the user
        """
        raise Exception('To be implemented by user')

    def apply_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache()):  # pragma: no cover
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

        Args:
          manifest_lookup_function: A function passed in by the ManifestManager. Called with `manifest_lookup_function(name='...')`. Implemented in ManifestManager.get_manifest_instance_by_name()
          variable_cache: A reference to the current instance of the VariableCache

        Returns:
            Any returned value will be ignored by the ManifestManager

        Raises:
            Exception: When the method was not implemented by th user
            Exception: As determined by the user
        """
        raise Exception('To be implemented by user')
    
    def delete_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache()):  # pragma: no cover
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

        Args:
          manifest_lookup_function: A function passed in by the ManifestManager. Called with `manifest_lookup_function(name='...')`. Implemented in ManifestManager.get_manifest_instance_by_name()
          variable_cache: A reference to the current instance of the VariableCache

        Returns:
            Any returned value will be ignored by the ManifestManager

        Raises:
            Exception: When the method was not implemented by th user
            Exception: As determined by the user
        """
        raise Exception('To be implemented by user')


class ManifestManager:

    def __init__(self, variable_cache: VariableCache, logger=get_logger()):
        self.manifest_class_register = dict()
        self.manifest_instances = dict()
        self.manifest_data_by_manifest_name = dict()
        self.variable_cache = variable_cache
        self.logger = logger

    def register_manifest_class(self, manifest: ManifestBase):
        if isinstance(manifest, ManifestBase) is False:
            raise Exception('Incorrect Base Class')
        idx = '{}:{}'.format(manifest.kind, manifest.version)
        self.manifest_class_register[idx] = manifest
        self.logger.info('Registered manifest "{}" of version {}'.format(manifest.__class__.__name__, manifest.version))
        for idx_sv in manifest.supported_versions:
            idx = '{}:{}'.format(manifest.kind, idx_sv)
            if idx not in self.manifest_class_register:
                self.manifest_class_register[idx] = manifest
                self.logger.info('Registered manifest "{}" of version {}'.format(manifest.__class__.__name__, manifest.version))

    def load_manifest_class_definition_from_file(self, plugin_file_path: str):
        for returned_class, kind in get_modules_in_package(target_dir=plugin_file_path, logger=self.logger):
             self.register_manifest_class(manifest=returned_class(logger=self.logger))
        self.logger.info('Registered classes: {}'.format(list(self.manifest_class_register.keys())))

    def get_manifest_instance_by_name(self, name: str):
        for key, manifest_instance in self.manifest_instances.items():
            if manifest_instance.metadata['name'] == name or '{}:{}:{}'.format(manifest_instance.metadata['name'],manifest_instance.version,manifest_instance.checksum) == name:
                return manifest_instance
        raise Exception('No manifest instance for "{}" found'.format(name))
    
    def apply_manifest(self, name: str):
        manifest_instance = self.get_manifest_instance_by_name(name=name)
        if 'skipApplyAll' in manifest_instance.metadata:
            if manifest_instance.metadata['skipApplyAll'] is True:
                self.logger.warning('ManifestManager:apply_manifest(): Manifest named "{}" skipped because of skipApplyAll setting'.format(manifest_instance.metadata['name']))
                return
        manifest_instance.process_dependencies(action='apply', manifest_lookup_function=self.get_manifest_instance_by_name, variable_cache=self.variable_cache)
        manifest_instance.apply_manifest(manifest_lookup_function=self.get_manifest_instance_by_name, variable_cache=self.variable_cache)

    def delete_manifest(self, name: str):
        manifest_instance = self.get_manifest_instance_by_name(name=name)
        if 'skipDeleteAll' in manifest_instance.metadata:
            if manifest_instance.metadata['skipApplyAll'] is True:
                self.logger.warning('ManifestManager:delete_manifest(): Manifest named "{}" skipped because of skipApplyAll setting'.format(manifest_instance.metadata['name']))
                return
        manifest_instance.process_dependencies(action='delete', manifest_lookup_function=self.get_manifest_instance_by_name, variable_cache=self.variable_cache)
        manifest_instance.delete_manifest(manifest_lookup_function=self.get_manifest_instance_by_name, variable_cache=self.variable_cache)

    def get_manifest_class_by_kind(self, kind: str, version: str=None):
        idx = kind
        if version is not None:
            idx = '{}:{}'.format(kind, version)
        else:
            versions_discovered = list()
            for versioned_manifest_idx in tuple(self.manifest_class_register.keys()):
                if versioned_manifest_idx.startswith('{}:'.format(kind)):
                    if versioned_manifest_idx not in versions_discovered:
                        versions_discovered.append(versioned_manifest_idx)
                    for supported_version_id in self.manifest_class_register[versioned_manifest_idx].supported_versions:
                        supported_version_key = '{}:{}'.format(kind, supported_version_id)
                        if supported_version_key not in versions_discovered:
                            versions_discovered.append(versioned_manifest_idx)
                        # versions_discovered may now have something like ['v1', 'v0.1', 'v2', 'v1.5']

            versions_discovered.sort()  # Based on the example, this will now be ['v0.1', 'v1', 'v1.5', 'v2']
            if len(versions_discovered) > 0:
                idx = versions_discovered[-1] # latest, expecting v2
            self.logger.debug('All versions registered for kind "{}": {}'.format(kind, versions_discovered))

        if idx in self.manifest_class_register:
            return self.manifest_class_register[idx]
        raise Exception('Manifest kind "{}" not registered'.format(kind))
    
    def parse_manifest(self, manifest_data: dict):
        manifest_data = dict((k.lower(), v) for k,v in manifest_data.items())   # Convert first level keys to lower case
        version = None
        if 'version' in manifest_data:
            version = manifest_data['version']
        class_instance_copy = copy.deepcopy(self.get_manifest_class_by_kind(kind=manifest_data['kind'], version=version))
        class_instance_copy.parse_manifest(manifest_data=manifest_data)
        idx = '{}:{}:{}'.format(
            class_instance_copy.metadata['name'],
            class_instance_copy.version,
            class_instance_copy.checksum
        )
        # self.manifest_instances[class_instance_copy.metadata['name']] = class_instance_copy
        self.logger.info('parse_manifest(): Stored parsed manifest instance "{}"'.format(idx))
        self.manifest_instances[idx] = class_instance_copy
        self.manifest_data_by_manifest_name[manifest_data['metadata']['name']] = manifest_data

