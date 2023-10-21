Quick Navigation: [Documentation home](../../../README.md) | [Up](../README.md)

<hr />

# `StreamHandlerLogging` Description
     
Logs to STDOUT

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

| Field                       | Type    | Required | Default Value                               | Description                                                                                 |
|-----------------------------|---------|----------|---------------------------------------------|---------------------------------------------------------------------------------------------|
| level                       | str     | No       | `info`                                      | The logging level                                                                           |
| loggingFormat               | str     | No       | `'%(asctime)s %(levelname)s - %(message)s'` | The message format. See https://docs.python.org/3/library/logging.html#logrecord-attributes |

# Example

## Basic Example

Sets the log level to `DEBUG` which means that if the `DEBUG` environment
variable is set, debug logging messages will be streamed to `STDOUT`.

The log format is also set to include various fields as defined in the 
[Python Log Format Documentation](https://docs.python.org/3/library/logging.html#logrecord-attributes)

```yaml
kind: StreamHandlerLogging
version: v1
metadata:
  name: StreamHandler
spec:
  level: debug
  loggingFormat: ' *** %(asctime)s %(levelname)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s'
```

# See Also

* [Syslog Logger](./02-syslog-logger.md)
* [Datagram Logger](./03-datagram-logger.md)
* [File Logger](./04-file-logger.md)
* [Rotating File Logger](./05-rotating-file-logger.md)

<hr />

Quick Navigation: [Documentation home](../../../README.md) | [Up](../README.md)