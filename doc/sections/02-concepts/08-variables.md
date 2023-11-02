Quick Navigation: [Documentation home](../../README.md) | [Up](./README.md)

<hr />

- [How are Variables defined](#how-are-variables-defined)
- [Standard Variables](#standard-variables)
- [See Also](#see-also)


# How are Variables defined
     
Each time an extension processes a manifest, it will generated a set of variables. Each extension defines a standard set of variables it will define and those should be documented with the extension.

See the documentation of [the _WriteFile_](../03-standard-extensions-documentation/03-other/05-write-file.md) extension for an example. In that extension the following variables are defined:

* `FILE_PATH` - The full path to the file
* `WRITTEN` - Boolean, where a TRUE value means the file was processed.
* `EXECUTABLE` - Boolean value which will be TRUE if the file has been set as executable
* `SIZE` - The file size in BYTES
* `SHA256_CHECKSUM` - The calculated file checksum (SHA256)

The variables can be used by using the `!Variable` custom YAML Tag. In the `WriteFile` documentation the following example can be examined:

```yaml
spec:
  data: !Sub
  - '{"status": "${status}","downloadPath": "${path}"}'
  - status: !Variable 'WebDownloadFile:web-download:STATUS'
    path: !Variable 'CliInputPrompt:save-target:CLI_INPUT_VALUE'
```

The line `!Variable 'WebDownloadFile:web-download:STATUS'` shows the typical syntax of a variable reference:

```text
WebDownloadFile:web-download:STATUS
\___._________/ \____._____/ \__._/
    |                |          |
  Kind        Manifest Name     |
                          Variable Name
                 (as defined by the Extension)
```

# Standard Variables

There are also a couple of standard variables that is available to reference:

| `!Variable` Reference | Description                                                                                  |
|-----------------------|----------------------------------------------------------------------------------------------|
| `std::action`         | Will have the value of `apply` or `delete` depending on how the animus processing is started |
| `std::scope`          | The scope name used in `metadata.environment` settings.                                      |

# See Also

* [What is a resource](./01-what-is-a-resource.md)
* [What is a "_Desired State_"](./02-what-is-desired-state.md)
* [Defining desired resource state in a Manifest](./03-defining-desired-resource-state-in-a-manifest.md)
* [Actions that can be performed to enforce resource state](./04-actions-that-can-be-performed-to-enforce-resource-state.md)
* [Extensions for every resources](./05-extensions-for-every-resources.md)
* [How to think of Environments](./06-environments.md)
* [How to use Values](./07-values.md)
* [Planning and Project Hierarchy, Dependencies and Other Consideration](./09-planning-and-hierarchy.md)

<hr />

Quick Navigation: [Documentation home](../../../README.md) | [Up](./README.md)