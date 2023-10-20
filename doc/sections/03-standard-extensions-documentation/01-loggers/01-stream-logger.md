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

```yaml
kind: StreamHandlerLogging
version: v1
metadata:
  name: StreamHandler
spec:
  level: !Value project-1-log-level
  loggingFormat: ' *** %(asctime)s %(levelname)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s'
```