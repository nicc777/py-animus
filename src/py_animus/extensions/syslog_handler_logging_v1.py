"""
    Copyright (c) 2023. All rights reserved. NS Coetzee <nicc777@gmail.com>

    This file is licensed under GPLv3 and a copy of the license should be included in the project (look for the file 
    called LICENSE), or alternatively view the license text at 
    https://raw.githubusercontent.com/nicc777/verbacratis/main/LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt
"""

from py_animus.models import all_scoped_values, variable_cache, Action, actions
from py_animus.animus_logging import logger, add_handler
from py_animus.models.extensions import ManifestBase
import logging
import logging.handlers
import sys
import socket


class SyslogHandlerLogging(ManifestBase):   # pragma: no cover
    """# `SyslogHandlerLogging` Description
     
Logs to Syslog (by default logs to local host). The Syslog service is expected
to listen on a specific UDP or TCP port. The type of port is set by the 
`socketType` option (default=DGRAM or UDP).

# Apply Action

Configures the logger

# Delete Action

Automatically redirects to the `apply` action

# Variables 

## After Apply Action

No variables are set

## After Delete Action

No variables are set or deleted

## Spec fields

| Field                       | Type    | Required | Default Value                               | Description                                     |
|-----------------------------|---------|----------|---------------------------------------------|-------------------------------------------------|
| level                       | string  | No       | `info`                                      | The logging level                               |
| loggingFormat               | string  | No       | `'%(asctime)s %(levelname)s - %(message)s'` | The message format                              |
| host                        | string  | No       | `localhost`                                 | The IP address or hostname of the Syslog server |
| port                        | integer | No       | `514`                                       | The port of the Syslog server                   |
| facility                    | string  | No       | `USER`                                      | The syslog facility                             |
| socketType                  | string  | No       | `DGRAM`                                     | The socket type                                 |

Supported `facility` names:

* `USER`
* `LOCAL0` upto and including `LOCAL7`

Supported `socketType` values:

* `DGRAM`
* `STREAM`

# Examples

## Basic Example

The following example demonstrates how to target a remote system server listening on a TCP port.

```yaml
kind: SyslogHandlerLogging
version: v1
metadata:
  name: syslog-logger
spec:
  host: my-syslog-server
  port: 1514
  socketType: STREAM
  facility: LOCAL1
```

# See Also

* [Console Logger](https://github.com/nicc777/py-animus/blob/main/doc/sections/03-standard-extensions-documentation/01-loggers/01-stream-logger.md)
* [Datagram Logger](https://github.com/nicc777/py-animus/blob/main/doc/sections/03-standard-extensions-documentation/01-loggers/03-datagram-logger.md)
* [File Logger](https://github.com/nicc777/py-animus/blob/main/doc/sections/03-standard-extensions-documentation/01-loggers/04-file-logger.md)
* [Rotating File Logger](https://github.com/nicc777/py-animus/blob/main/doc/sections/03-standard-extensions-documentation/01-loggers/05-rotating-file-logger.md)
    """

    def __init__(self, post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def implemented_manifest_differ_from_this_manifest(self)->bool:
        if actions.get_action_status(manifest_kind=self.kind, manifest_name=self.metadata['name'], action_name='Configure SyslogHandler Logging') == Action.APPLY_DONE:
            return False
        return True
    
    def determine_actions(self)->list:
        self.register_action(action_name='Configure SyslogHandler Logging', initial_status=Action.UNKNOWN)
        if self.implemented_manifest_differ_from_this_manifest() is True:
            self.register_action(action_name='Configure SyslogHandler Logging', initial_status=Action.APPLY_PENDING)
        return actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name'])

    def _configure_logging(self):

        # Defaults
        host = 'localhost'
        port = 514
        facility = logging.handlers.SysLogHandler.LOG_USER
        syslog_socket = socket.SOCK_DGRAM
        log_format = '%(asctime)s %(levelname)s - %(message)s'
        log_level = logging.INFO

        # Spec overrides
        if 'host' in self.spec:
            host = self.spec['host']
        if 'port' in self.spec:
            port = int(self.spec['host'])
        if 'facility' in self.spec:
            if self.spec['facility'].upper() in 'LOCAL0':
                facility = logging.handlers.SysLogHandler.LOG_LOCAL0
            if self.spec['facility'].upper() == 'LOCAL1':
                facility = logging.handlers.SysLogHandler.LOG_LOCAL1
            if self.spec['facility'].upper() == 'LOCAL2':
                facility = logging.handlers.SysLogHandler.LOG_LOCAL2
            if self.spec['facility'].upper() == 'LOCAL3':
                facility = logging.handlers.SysLogHandler.LOG_LOCAL3
            if self.spec['facility'].upper() == 'LOCAL4':
                facility = logging.handlers.SysLogHandler.LOG_LOCAL4
            if self.spec['facility'].upper() == 'LOCAL5':
                facility = logging.handlers.SysLogHandler.LOG_LOCAL5
            if self.spec['facility'].upper() == 'LOCAL6':
                facility = logging.handlers.SysLogHandler.LOG_LOCAL6
            if self.spec['facility'].upper() == 'LOCAL7':
                facility = logging.handlers.SysLogHandler.LOG_LOCAL7
        if 'socketType' in self.spec:
            if self.spec['socketType'].upper() == 'STREAM':
                syslog_socket = socket.SOCK_STREAM
        if 'level' in self.spec:
            if self.spec['level'].lower().startswith('d') is True:
                log_level = logging.DEBUG
            if self.spec['level'].lower().startswith('e') is True:
                log_level = logging.ERROR
            if self.spec['level'].lower().startswith('c') is True:
                log_level = logging.CRITICAL
        if 'loggingFormat' in self.spec:
            log_format = self.spec['loggingFormat']

        # Logger setup
        formatter = logging.Formatter(log_format)
        h = logging.handlers.SysLogHandler(address=(host, port), facility=facility, socktype=syslog_socket)
        h.setLevel(log_level)
        h.setFormatter(formatter)
        add_handler(h)

    def apply_manifest(self): 
        for action_name, expected_action in actions.get_action_values_for_manifest(manifest_kind=self.kind, manifest_name=self.metadata['name']).items():
            if action_name == 'Configure SyslogHandler Logging' and expected_action == Action.APPLY_PENDING:
                self._configure_logging()
                actions.add_or_update_action(action=Action(manifest_kind=self.kind, manifest_name=self.metadata['name'], action_name='Configure SyslogHandler Logging', action_status=Action.APPLY_DONE))
        logger.debug('SyslogHandlerLogging configuration done')
        return
    
    def delete_manifest(self):
        self.log(message='Logging "delete" actions automatically redirects to an apply action.', level='warning')
        return self.apply_manifest()

