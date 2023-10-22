Quick Navigation: [Documentation home](../../../README.md) | [Up](./README.md)

<hr />

# `FileHandlerLogging` Description
     
Logs to a file on the local system. The log file will be appended to 
indefinitely. No rotation is performed with this logging extension. For 
rotation of log files, consider the `RotatingFileHandlerLogging` 
extension.

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

| Field                       | Type    | Required | Default Value                               | Description        |
|-----------------------------|---------|----------|---------------------------------------------|--------------------|
| level                       | str     | No       | `info`                                      | The logging level  |
| loggingFormat               | str     | No       | `'%(asctime)s %(levelname)s - %(message)s'` | The message format |
| filename                    | str     | yes      | None (will cause Exception to be raised)    | The log file name  |

# Examples

## Basic Example

The following example illustrate how to target a specific log file with the `DEBUG` log level set:

```yaml
kind: FileHandlerLogging
version: v1
metadata:
  name: file-logger
spec:
  filename: /tmp/my-logger
  level: debug
```

# See Also

* [Console Logger](./01-stream-logger.md)
* [Syslog Logger](./02-syslog-logger.md)
* [Datagram Logger](./03-datagram-logger.md)
* [Rotating File Logger](./05-rotating-file-logger.md)

<hr />

Quick Navigation: [Documentation home](../../../README.md) | [Up](./README.md)