Quick Navigation: [Documentation home](../../README.md) | [Up](./README.md)

<hr />

- [Actions that can be performed to enforce resource state](#actions-that-can-be-performed-to-enforce-resource-state)
- [How Extensions Interpret and Act on Actions](#how-extensions-interpret-and-act-on-actions)
- [See Also](#see-also)

# Actions that can be performed to enforce resource state
     
These are the actions that `py-animus` supports at the moment:

| Action    | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `apply`   | The intention of this action is to create resources. For previously created resources, the intention is to first see if the current implementation differ from what is expressed in the manifest and then to apply the necessary changes to align the current resource configuration with what is expressed in the manifest. Depending on the implementation of the extension, it may be required that a new resource be created and the old resource deleted. |
| `delete`  | The intention of this action is to first identify if the resource defined in the manifest was previously provisioned, and then - if it was - delete it.                                                                                                                                                                                                                                                                                                        |

More actions may be added in the future.

# How Extensions Interpret and Act on Actions

Each extension implements every action based on the intent of that extension which should be well documented in each extension.

For the included extensions refer to the [extension documentation](../03-standard-extensions-documentation/README.md).

Not all extensions may always actually create something. There can also be helper extensions that aims to be an interim step that gathers information or configures a certain third party client that may be required for other extensions to re-use. There are a number of these extensions included in the standard `py-animus` package, including the following:

| Extension                                                                                      | Use Case                                                                                                                                                                                                                                            |
|------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Any of the [logging](../03-standard-extensions-documentation/01-loggers/README.md) extensions. | Allows users to have fine grain control over logging while `py-animus` executes the desired action.                                                                                                                                                 |
| The `Project` and `Values` special manifests                                                   | These manifests do not really have extensions and their implementation is the bases of`py-animus`.                                                                                                                                                  |
| `CliInputPrompt`                                                                               | This extension can be used when user input from the terminal/console is required.                                                                                                                                                                   |
| `ShellScript`                                                                                  | Allows users to run any arbitrary shell script command which may or may not create/delete resources.                                                                                                                                                |
| `GitRepo`                                                                                      | Handy for cloning/or pulling updates from a remote Git repository. The repository may include other resources required for further processing, like additional manifests or additional artifacts required for use by other extensions.              |
| `WebDownloadFile`                                                                              | Similar to the `GitRepo` extensions, intended to download a single file from a web URL.                                                                                                                                                             |
| `WriteFile`                                                                                    | Creates/deletes a files on the local system where `py-animus` is running. Handy for generating reports. See [this example](../../../examples/projects/download_web_page_supplied_by_user_input/tasks.yaml) of how a simple report can be generated. |


# See Also

* [What is a resource](./01-what-is-a-resource.md)
* [What is a "_Desired State_"](./02-what-is-desired-state.md)
* [Defining desired resource state in a Manifest](./03-defining-desired-resource-state-in-a-manifest.md)
* [Extensions for every resources](./05-extensions-for-every-resources.md)
* [How to think of Environments](./06-environments.md)
* [How to use Values](./07-values.md)
* [Using Variables](./08-variables.md)
* [Planning and Project Hierarchy, Dependencies and Other Consideration](./09-planning-and-hierarchy.md)

<hr />

Quick Navigation: [Documentation home](../../../README.md) | [Up](./README.md)