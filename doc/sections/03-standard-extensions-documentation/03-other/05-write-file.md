Quick Navigation: [Documentation home](../../../README.md) | [Up](../README.md)

<hr />

# `WriteFile` Description
     
This manifest will take provided data and write it to a file. The file can be 
(optionally) marked as executable.

The `apply` action will create the file and the `delete` action will delete the
file. To retain files on `delete` action, set the manifest skip option in the 
meta data.

# Apply Action

Get input from user

# Delete Action

No Action

# Variables 

## After Apply Action

The following variables will be defined:

* `FILE_PATH` - The full path to the file
* `WRITTEN` - Boolean, where a TRUE value means the file was processed.
* `EXECUTABLE` - Boolean value which will be TRUE if the file has been set as executable
* `SIZE` - The file size in BYTES
* `SHA256_CHECKSUM` - The calculated file checksum (SHA256)

## After Delete Action

The following variables will be deleted:

* `FILE_PATH`
* `WRITTEN`
* `EXECUTABLE`
* `SIZE`
* `SHA256_CHECKSUM`

## Spec fields

Spec fields:

| Field                        | Type     | Required | Default Value  | Description                                                                                                                                 |
|------------------------------|----------|----------|----------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| `targetFile`                 | str      | Yes      | n/a            | Full path to a file                                                                                                                         |
| `data`                       | str      | Yes      | n/a            | The actual content of the file. Typically a `Value` or `Variable` reference will be used here                                               |
| `actionIfFileAlreadyExists`  | str      | No       | `overwrite`    | Allowed values: overwrite (write the data to the file anyway - overwriting any previous data), skip (leave the current file as is and skip) |
| `fileMode`                   | str      | No       | `normal`       | Allowed values: normal (chmod 600) or executable (chmod 700)                                                                                |
   

# Examples

## Basic Example

The following example is taken from `examples/projects/download_web_page_supplied_by_user_input/tasks.yaml` and will create a file on the local file system `/tmp/results.json`. The variables placeholders will be replaced by the calculated values at runtime.

```yaml
---
kind: WriteFile
version: v1
metadata:
  name: write-file-v1-minimal
  dependencies:
    apply:
    - web-download
    - cleanup-all-done-file
    delete:
    - cleanup-all-done-file
spec:
  data: !Sub
  - '{"status": "${status}","downloadPath": "${path}"}'
  - status: !Variable 'WebDownloadFile:web-download:default:STATUS'
    path: !Variable 'CliInputPrompt:save-target:default:CLI_INPUT_VALUE'
  targetFile: /tmp/results.json
```

# See Also

* [CLI Input](./03-other/01-cli-input.md)
* [Shell Script](./03-other/02-shell-script.md)
* [Git Repository](./03-other/03-git-repo.md)
* [Web Resource Download](./03-other/04-web-download.md)

<hr />

Quick Navigation: [Documentation home](../../../README.md) | [Up](../README.md)