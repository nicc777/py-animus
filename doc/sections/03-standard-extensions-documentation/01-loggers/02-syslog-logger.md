Quick Navigation: [Documentation home](../../../README.md) | [Up](./README.md)

<hr />

# `SyslogHandlerLogging` Description
     
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
```

# See Also

* [Console Logger](./01-stream-logger.md)
* [Datagram Logger](./03-datagram-logger.md)
* [File Logger](./04-file-logger.md)
* [Rotating File Logger](./05-rotating-file-logger.md)

<hr />

Quick Navigation: [Documentation home](../../../README.md) | [Up](./README.md)