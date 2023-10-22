Quick Navigation: [Documentation home](../../../README.md) | [Up](./README.md)

<hr />

# `RotatingFileHandlerLogging` Description
     
Logs to a file on the local system. The log file will be appended until 
`maxBytes` is reached (default=10 MiB). The number of backups kept is 
determined by the `backupCount` setting (default=5).

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

| Field                       | Type    | Required | Default Value                               | Description                                                  |
|-----------------------------|---------|----------|---------------------------------------------|--------------------------------------------------------------|
| level                       | str     | No       | `info`                                      | The logging level                                            |
| loggingFormat               | str     | No       | `'%(asctime)s %(levelname)s - %(message)s'` | The message format                                           |
| filename                    | str     | yes      | None (will cause Exception to be raised)    | The log file name                                            |
| maxBytes                    | int     | No       | 10 MiB                                      | How many bytes to log before rotating the log file           |
| backupCount                 | int     | No       | 5                                           | HOw many files to keep before starting to delete old files.  | 

# Examples

## Basic Example

The following example specifies a specific file that will only be rotated once 1 GB is reached with a backup count of 2 files:

```yaml
kind: RotatingFileHandlerLogging
version: v1
metadata:
  name: rotating-file-logger-abc
spec:
  filename: /some/path/to/logs/project-abc.log
  maxBytes: 1080042496 # 1 GiB per log file
  backupCount: 2
```

# See Also

* [Console Logger](./01-stream-logger.md)
* [Syslog Logger](./02-syslog-logger.md)
* [Datagram Logger](./03-datagram-logger.md)
* [File Logger](./04-file-logger.md)

<hr />

Quick Navigation: [Documentation home](../../../README.md) | [Up](./README.md)