
Quick Navigation: [Documentation home](../../README.md) | [Up](./README.md)

<hr />

- [Command Line Arguments](#command-line-arguments)
- [See Also](#see-also)

# Command Line Arguments

Assuming you have [installed](./01-installing.md) `py-animus` in a [Python Virtual Environment](https://docs.python.org/3/library/venv.html), refer to the following example:

```shell
venv/bin/animus apply /path/to/my/project.yaml my-project my-environment
```

Breaking this line down in to it's individual components:

| String                     | Expected Value                                                                                                                                                                                                                                                           |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `venv/bin/animus`          | Points to the binary where `py-animus` was installed                                                                                                                                                                                                                     |
| `apply`                    | The action, which can be `apply` or `delete`. Refer also to the [further documentation](../02-concepts/04-actions-that-can-be-performed-to-enforce-resource-state.md) about actions.                                                                                     |
| `/path/to/my/project.yaml` | Path to the YAML file to use as starting point. Can also be a url starting with HTTP or HTTPS. This manifest file _MUST_ contain the project manifest referenced by name next. [more about projects](../02-concepts/03-defining-desired-resource-state-in-a-manifest.md) |
| `my-project`               | The name (`metadata.name` value) of the Project Manifest contained in the referenced file/URL.                                                                                                                                                                           |
| `my-environment`           | The [environment](../02-concepts/06-environments.md) to target for this project using the specified action.                                                                                                                                                              |

> **note**
> The above is currently the only format supported to start `py-animus` but this may change in the future.

# See Also

* [Installing](./01-installing.md)
* [First project and capability demonstration](./02-first-project-and-capability-demonstration.md)

<hr />

Quick Navigation: [Documentation home](../../README.md) | [Up](./README.md)