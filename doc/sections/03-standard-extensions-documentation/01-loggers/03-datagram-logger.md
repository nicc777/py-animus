Quick Navigation: [Documentation home](../../../README.md) | [Up](./README.md)

<hr />

# `DatagramHandlerLogging` Description
     
Logs to a UDP port on a remote host

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

| Field                       | Type    | Required | Default Value                               | Description                                           |
|-----------------------------|---------|----------|---------------------------------------------|-------------------------------------------------------|
| level                       | string  | No       | `info`                                      | The logging level                                     |
| loggingFormat               | string  | No       | `'%(asctime)s %(levelname)s - %(message)s'` | The message format                                    |
| host                        | string  | Yes      | None (will cause Exception to be raised)    | The IP address or hostname of the UDP listener server |
| port                        | integer | Yes      | None (will cause Exception to be raised)    | The port of the UDP listener server                   |

# Examples

## Basic Example

The following example is a basic example that specify a target host and the log level:

```yaml
kind: DatagramHandlerLogging
version: v1
metadata:
  name: datagram-logger
spec:
  host: my-datagram-logger-host
  level: debug
```

# See Also

* [Console Logger](./01-stream-logger.md)
* [Syslog Logger](./02-syslog-logger.md)
* [File Logger](./04-file-logger.md)
* [Rotating File Logger](./05-rotating-file-logger.md)

<hr />

Quick Navigation: [Documentation home](../../../README.md) | [Up](./README.md)