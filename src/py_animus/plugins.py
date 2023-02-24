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
from py_animus import get_logger, get_utc_timestamp, is_debug_set_in_environment


def dummy_manifest_lookup_function(name: str):
    return


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
        self._log_debug(message='elapsed_time={}   ttl={}'.format(elapsed_time, self.ttl))
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


class ManifestBase:

    def __init__(self, logger=get_logger(), post_parsing_method: object=None):
        self.spec = None
        self.kind = self.__class__.__name__
        self.metadata = dict()
        self.version = 'v1'
        self.supported_versions = [self.version, ]
        self.debug = is_debug_set_in_environment()
        self.logger = logger
        self.initialized = False
        self.post_parsing_method = post_parsing_method
        self.checksum = None

    def log(self, message: str, level: str='info'): # pragma: no cover
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
        converted_data = dict((k.lower(),v) for k,v in manifest_data.items()) # Convert keys to lowercase
        if 'kind' in converted_data:
            if converted_data['kind'] != self.kind:
                self.log(message='Kind mismatch. Got "{}" and expected "{}"'.format(converted_data['kind'], self.kind), level='error')
                return
        else:
            self.log(message='Kind property not present in data. Data={}'.format(manifest_data), level='error')
            raise Exception('Kind property not present in data.')
        if 'version' in converted_data:
            if converted_data['version'] not in self.supported_versions:
                self.log(message='Version {} not supported by this implementation. Supported versions: {}'.format(converted_data['version'], self.supported_versions), level='error')
                raise Exception('Version {} not supported by this implementation.'.format(converted_data['version']))
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

    def to_dict(self):
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
        return yaml.dump(self.to_dict())

    def implemented_manifest_differ_from_this_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function)->bool:
        raise Exception('To be implemented by user')

    def apply_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function):
        raise Exception('To be implemented by user')


