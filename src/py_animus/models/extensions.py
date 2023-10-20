"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""
import traceback
import copy
import json
import hashlib
import yaml
import re
from py_animus.helpers import is_debug_set_in_environment
# from py_animus.animus_logging import logger
import py_animus.animus_logging
from py_animus.models import actions, Action, scope, variable_cache


SUPPORTED_TYPES = (
    str,
    int,
    float,
    list,
    dict,
)


def convert_list_items_to_serializable_objects(data: list, dict_conversion_function: object)->list:
    converted = list()
    for v in data:
        if isinstance(v,dict) is True:
            converted.append(dict_conversion_function(data=v))
        elif isinstance(v, list) is True or isinstance(v, tuple) is True:
            converted.append(convert_list_items_to_serializable_objects(data=v, dict_conversion_function=convert_dict_items_to_serializable_objects))
        elif type(v) not in SUPPORTED_TYPES:
            converted.append(str(v))
        else:
            converted.append(v)
    return converted


def convert_dict_items_to_serializable_objects(data: dict)->dict:
    converted = dict()
    for k,v in data.items():
        if isinstance(v,dict) is True:
            converted[k] = convert_dict_items_to_serializable_objects(data=v)
        elif isinstance(v, list) is True or isinstance(v, tuple) is True:
            converted[k] = convert_list_items_to_serializable_objects(data=v, dict_conversion_function=convert_dict_items_to_serializable_objects)
        elif type(v) not in SUPPORTED_TYPES:
            converted[k] = str(v)
        else:
            converted[k] = v
    return converted


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
        self.done_status_values = (
            Action.APPLY_ABORTED_WITH_ERRORS,
            Action.APPLY_DONE,
            Action.APPLY_SKIP,
            Action.DELETE_ABORTED_WITH_ERRORS,
            Action.DELETE_DONE,
            Action.DELETE_SKIP,
        )
        self.logger = py_animus.animus_logging.logger
        self.extension_action_descriptions = ('Generic Action',)

    def _var_name(self, var_name: str):
        return '{}:{}:{}:{}'.format(
            self.__class__.__name__,
            self.metadata['name'],
            scope.value,
            var_name
        )

    def _get_variable_name_from_full_variable_string(self, input_str: str)->dict:
        variables = dict()
        all_variable_names = variable_cache.get_all_current_names()
        self.log(message='         all_variable_names      : {}'.format(all_variable_names), level='debug')
        if '!Variable' in input_str:
            self.log(message='         FOUND variable input_str', level='debug')
            sections = input_str.split('!Variable') # NOTE: There may be MORE than one variable in a single line...
            self.log(message='         sections : {}'.format(sections), level='debug')
            self.log(message='            QTY   : {}'.format(len(sections)), level='debug')
            if len(sections) > 1:
                sections_qty = len(sections)
                self.log(message='         sections_qty: {}'.format(sections_qty), level='debug')
                for section in sections:
                    self.log(message='         Parsing sections', level='debug')
                    variable_name = '{}'.format(section)
                    variable_name.strip()
                    self.log(message='            variable_name interim value: "{}"'.format(variable_name), level='debug')
                    result = re.search(r"([\w|\:|\-]+)", variable_name)
                    try:
                        if len(result.groups()) > 0:
                            self.log(message='            Extracting group 0 for variable_name in regex groups'.format(variable_name), level='debug')
                            variable_name = result.groups()[0]

                            if variable_name in all_variable_names:
                                original_variable_str = '!Variable {}'.format(variable_name)
                                original_variable_str = original_variable_str.replace('  ', ' ')
                                original_variable_str = original_variable_str.strip()
                                self.log(message='            original_variable_str: {}'.format(original_variable_str), level='debug')
                                self.log(message='            FINAL variable_name "{}"'.format(variable_name), level='debug')
                                if original_variable_str not in variables:
                                    self.log(message='         Added variable to variables DICT', level='debug')
                                    variables[original_variable_str] = variable_name
                                else:
                                    self.log(message='            Not adding variable to variables DICT - already exists', level='debug')
                        else:
                            self.log(message='            No REGEX match for variable name...'.format(variable_name), level='debug')
                    except AttributeError:
                        self.log(message='No groups found in regex', level='error')
                    except:
                        self.log(message='EXCEPTION: {}'.format(traceback.format_exc()), level='error')
            else:
                self.log(message='         No sections to parse', level='debug')
        else:
            self.log(message='         NO variable found in input_str', level='debug')
        self.log(message='         input_str={}   variables: {}'.format(input_str, json.dumps(variables, default=str)), level='debug')
        return variables

    def resolve_all_pending_variables(self, iterable):
        resolved_iterable = None
        self.log(message='Resolving data in iterable: {}'.format(iterable), level='debug')
        if isinstance(iterable, dict):
            self.log(message='   DICT detected', level='debug')
            resolved_iterable = dict()
            for k,v in iterable.items():
                final_value = copy.deepcopy(v)
                self.log(message='   k: {}'.format(k), level='debug')
                self.log(message='   v: {}'.format(v), level='debug')
                if isinstance(v, str):
                    self.log(message='      Identifying variable in string...', level='debug')
                    variables = self._get_variable_name_from_full_variable_string(input_str=v)
                    if len(variables) > 0:
                        for original_variable_str, variable_name in variables.items():
                            self.log(message='         original_variable_str={}   variable name identified as "{}"'.format(original_variable_str, variable_name), level='debug')
                            if variable_name is not None:
                                self.log(message='         Resolving variable_name "{}"'.format(variable_name), level='debug')
                                resolved_value = variable_cache.get_value(variable_name=variable_name, unresolved_variables_returns_original_reference=True)
                                self.log(message='         resolved_value={}'.format(resolved_value), level='debug')
                                final_value = final_value.replace(original_variable_str, resolved_value)
                                resolved_iterable[k] = final_value
                                self.log(message='            RESULT: {}={}'.format(k, final_value), level='debug')
                            else:
                                self.log(message='         No Variable to resolve found in string', level='debug')
                                resolved_iterable[k] = v
                    else:
                        self.log(message='         No Variable to resolve found in string', level='debug')
                        resolved_iterable[k] = v
                elif isinstance(v, dict) or isinstance(v, list) or isinstance(v, tuple):
                    resolved_iterable[k] = self.resolve_all_pending_variables(iterable=v)
                else:
                    resolved_iterable[k] = v
        elif isinstance(iterable, list) or isinstance(iterable, tuple):
            self.log(message='   LIST detected', level='debug')
            resolved_iterable = list()
            for v in iterable:
                final_value = copy.deepcopy(v)
                self.log(message='   v: {}'.format(v), level='debug')
                if isinstance(v, str):
                    self.log(message='      Identifying variable in string...', level='debug')
                    variables = self._get_variable_name_from_full_variable_string(input_str=v)
                    if len(variables) > 0:
                        for original_variable_str, variable_name in variables.items():
                            self.log(message='         original_variable_str={}   variable name identified as "{}"'.format(original_variable_str, variable_name), level='debug')
                            if variable_name is not None:
                                self.log(message='         Resolving variable_name "{}"'.format(variable_name), level='debug')
                                resolved_value = variable_cache.get_value(variable_name=variable_name, unresolved_variables_returns_original_reference=True)
                                self.log(message='         resolved_value={}'.format(resolved_value), level='debug')
                                final_value = final_value.replace(original_variable_str, resolved_value)
                                resolved_iterable.append(final_value)
                                self.log(message='            RESULT: {}'.format(final_value), level='debug')
                            else:
                                self.log(message='         No Variable to resolve found in string', level='debug')
                                resolved_iterable.append(v)
                    else:
                        self.log(message='         No Variable to resolve found in string', level='debug')
                        resolved_iterable.append(v)
                elif isinstance(v, dict) or isinstance(v, list) or isinstance(v, tuple):
                    resolved_iterable.append(self.resolve_all_pending_variables(iterable=v))
                else:
                    resolved_iterable.append(v)
            if isinstance(iterable, tuple):
                resolved_iterable = tuple(resolved_iterable)
        return resolved_iterable

    def register_action(self, action_name: str, initial_status: str=Action.UNKNOWN):
        """
        This should be called during the determine_Actions() method processing

        Args:
          action_name: A String with a name for a action, for example "Create Some File"
          initial_status: String with the initial status as defined in the Action class
        """
        actions.add_or_update_action(action=Action(manifest_kind=self.kind, manifest_name=self.metadata['name'], action_name=action_name, action_status=initial_status))

    def log(self, message: str, level: str='info'): # pragma: no cover
        """During implementation, calls to `self.log()` can be made to log messages using the configure logger.

        The log level is supplied as an argument, with the default level being 'info'

        Args:
          message: A String with the message to log
          level: The log level, expressed as a string. One of `info`, `error`, `debug` or `warning`
        """
        name = 'not-yet-known'
        if self.logger is None:
            self.logger = py_animus.animus_logging.logger
            self.logger.info('self.logger was None but is now configured')
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

    def logger_reset(self, new_logger):
        self.logger = new_logger
        self.log(message='Logger for "{}" reloaded'.format(self.kind), level='info')
        self.log(message='Logger for "{}" reloaded'.format(self.kind), level='debug')

    def parse_manifest(self, manifest_data: dict):
        """Called via the ManifestManager when manifests files are parsed and one is found to belong to a class of this implementation.

        The user does not have to override this implementation.

        Args:
          manifest_data: A Dictionary of data from teh parsed Manifest file
        """
        self.target_environments = ['default',]
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
            if 'environments' in self.metadata:
                self.target_environments = self.metadata['environments']
        if 'name' not in self.metadata:
            self.metadata['name'] = self.kind
            self.log(message='MetaData not supplied - using class Kind as name', level='warning')
        if 'spec' in converted_data:
            self.spec = convert_dict_items_to_serializable_objects(data=converted_data['spec'])
        self.initialized = True
        if self.post_parsing_method is not None:
            try:
                self.post_parsing_method(**self.__dict__)
            except:
                self.log(message='post_parsing_method failed with EXCEPTION: {}'.format(traceback.format_exc()), level='error')

        converted_data = convert_dict_items_to_serializable_objects(data=converted_data)

        self.checksum = hashlib.sha256(json.dumps(converted_data, sort_keys=True, ensure_ascii=True).encode('utf-8')).hexdigest() # Credit to https://stackoverflow.com/users/2082964/chris-maes for his hint on https://stackoverflow.com/questions/6923780/python-checksum-of-a-dict
        self.log(
            message='\n\nPOST PARSING. Manifest kind "{}" named "{}":\n   metadata: {}\n   spec: {}\n\n'.format(
                self.kind,
                self.metadata['name'],
                json.dumps(self.metadata),
                json.dumps(converted_data)
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

    def implemented_manifest_differ_from_this_manifest(self)->bool:    # pragma: no cover
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

    def _bulk_register_actions(self, final_action: str):
        for action_description in self.extension_action_descriptions:
            self.register_action(action_name='{}'.format(action_description), initial_status=final_action)
            self.log(message='Registered action "{}" with status "{}"'.format(action_description, final_action), level='info')

    def determine_actions(self, action_override: str=None, rerouted: bool=False):
        """
            This is a generic function which can be overridden for finer 
            grained control in extensions withy multiple actions.

        """
        final_Action = copy.deepcopy(actions.command)
        if action_override is not None:
            if action_override in ('apply', 'delete',):
                final_Action = action_override
        if final_Action == 'delete':
            if 'skipDeleteAll' in self.metadata and rerouted is False:
                if self.metadata['skipDeleteAll'] is True:
                    self._bulk_register_actions(final_action=Action.DELETE_SKIP)
                    return
        if final_Action == 'apply':
            if 'skipApplyAll' in self.metadata:
                if self.metadata['skipApplyAll'] is True and rerouted is False:
                    self._bulk_register_actions(final_action=Action.APPLY_SKIP)
                    return
        if self.implemented_manifest_differ_from_this_manifest() is True:
            if final_Action == 'apply':
                self._bulk_register_actions(final_action=Action.APPLY_PENDING)
            elif final_Action == 'delete':
                self._bulk_register_actions(final_action=Action.DELETE_PENDING)
            else:
                raise Exception('Unknown or unsupported command for this manifest kind "{}"'.format(self.kind))
        else:
            if final_Action == 'apply':
                self._bulk_register_actions(final_action=Action.APPLY_SKIP)
            elif final_Action == 'delete':
                self._bulk_register_actions(final_action=Action.DELETE_SKIP)
            else:
                raise Exception('Unknown or unsupported command for this manifest kind "{}"'.format(self.kind))
        return

    def apply_manifest(self):  # pragma: no cover
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
    
    def delete_manifest(self):  # pragma: no cover
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

