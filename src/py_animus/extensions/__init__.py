"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

from py_animus.extensions.stream_handler_logging_v1 import StreamHandlerLogging as StreamHandlerLoggingV1
from py_animus.extensions.file_handler_logging_v1 import FileHandlerLogging as FileHandlerLoggingV1
from py_animus.extensions.syslog_handler_logging_v1 import SyslogHandlerLogging as SyslogHandlerLoggingV1
from py_animus.extensions.datagram_handler_logging_v1 import DatagramHandlerLogging as DatagramHandlerLoggingV1
from py_animus.extensions.shell_script_v1 import ShellScript as ShellScriptV1
from py_animus.animus_logging import logger
from py_animus.models.extensions import ManifestBase
import copy


class AnimusExtensions:

    def __init__(self):
        self.extensions = dict()
        self.supported_versions_of_extensions = dict()

    def add_extension(self, extension: ManifestBase):
        if extension is None:
            return
        try:
            extension.__name__     # If this works, extension was not Initialized
        except:
            pass
        initialized_extension = extension()
        initialized_extension_kind = copy.deepcopy(initialized_extension.kind)
        version = copy.deepcopy(initialized_extension.version)
        idx = '{}:{}'.format(initialized_extension_kind, version)
        if idx not in self.extensions:
            self.extensions[idx] = extension
        if idx not in self.supported_versions_of_extensions:
            self.supported_versions_of_extensions[idx] = copy.deepcopy(initialized_extension.supported_versions)
        # return self

    def find_extension_that_supports_version(self, extension_kind: str, version: str)->ManifestBase:
        idx = '{}:{}'.format(extension_kind, version)
        if idx in self.extensions:
            return copy.deepcopy(self.extensions[idx])
        for idx, supported_versions in self.supported_versions_of_extensions.items():
            available_extension_kind = idx.split(':')[0]
            if available_extension_kind == extension_kind:
                if version in supported_versions:
                    return copy.deepcopy(self.extensions[idx])
        raise Exception('Extension kind "{}" of version "{}" was not found'.format(extension_kind, version))
                

extensions = AnimusExtensions()

# Add standard extensions
extensions.add_extension(extension=StreamHandlerLoggingV1)
extensions.add_extension(extension=FileHandlerLoggingV1)
extensions.add_extension(extension=SyslogHandlerLoggingV1)
extensions.add_extension(extension=DatagramHandlerLoggingV1)
extensions.add_extension(extension=ShellScriptV1)

