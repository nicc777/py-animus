Quick Navigation: [Documentation home](../../README.md) | [Up](./README.md)

<hr />

- [Defining desired resource state in a Manifest](#defining-desired-resource-state-in-a-manifest)
  - [Standard Manifest Fields](#standard-manifest-fields)
  - [Metadata Fields](#metadata-fields)
    - [Action Overrides](#action-overrides)
      - [Use case: Run a `ShellScript` command to backup a directory during a `delete` action that will delete the directory](#use-case-run-a-shellscript-command-to-backup-a-directory-during-a-delete-action-that-will-delete-the-directory)
    - [Dependencies](#dependencies)
  - [Spec Fields](#spec-fields)
- [Special Manifests](#special-manifests)
- [Project(s)](#projects)
  - [Project Dependencies](#project-dependencies)
  - [Project Spec](#project-spec)
- [See Also](#see-also)


# Defining desired resource state in a Manifest
     
In `py-animus`, all [desired state](./02-what-is-desired-state.md) is defined through a [YAML](https://en.wikipedia.org/wiki/YAML) (wikipedia) manifest.

The standard structure of the manifest below shows all the minimum required fields:

```yaml
---
kind: SomeKind
version: v1
metadata:
  name: manifest-name
spec:
  field: some-value
```

## Standard Manifest Fields

The following table shows the descriptions of the minimum set of fields that must make up a manifest:

| Field          | Description                                                                                                                                                                                                                                     |
|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `kind`         | Defines the kind of [resource](./01-what-is-a-resource.md) bound to an [extension](./05-extensions-for-every-resources.md) that is responsible for ensuring the [desired state](./02-what-is-desired-state.md) as defined in the `spec` section |
| `version`      | There may be several implementations of the same `kind` and each implementation is versioned. This version therefore indicates which version of the extension implementation to use to process this manifest.                                   |
| `metadata`     | Defines metadata of for the manifest. The `name` field is the only required field in this section. Names are important as they are used to link manifest in a dependency hierarchy.                                                             |
| `spec`         | THe fields in this section is dictated by the extension implementation. Have a look at the [`ShellScript` extension](../03-standard-extensions-documentation/03-other/02-shell-script.md) documentation for an example.                         |

## Metadata Fields

In the processing of manifests, the `metadata` defined fields and values is used to control the overall flow and order of processing manifests. As such, the bulk of the fields in this section deals with flow control and processing order.

Below is a table with all the available fields for `metadata`:

| Field              | Type            | Description                                                                                                                                                                                                                                                                                                                                                                                        |
|--------------------|-----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `name`             | String          | As already mentioned, names are important for referencing dependant manifests.                                                                                                                                                                                                                                                                                                                     |
| `skipApplyAll`     | Boolean         | If the `apply` action is called and this field value is `true`, the manifest will NOT be processed. This is useful for applying cert6ain manifests only during `delete` actions. A good use case is a manifest to delete the contents of an AWS S3 bucket before deleting the entire bucket. This action is only required during a `delete` action and can therefore be ignored in `apply` actions |
| `skipDeleteAll`    | Boolean         | Basically the opposite of the `skipApplyAll` meaning: manifests will only be processed when the `apply` action is run and will be ignored during `delete` actions.                                                                                                                                                                                                                                 |
| `environments`     | List of Strings | Refer to the [environments explanation](./06-environments.md) page for a full definition.                                                                                                                                                                                                                                                                                                          |
| `actionOverrides`  | Object          | May contain the object `delete: apply` or `apply: delete`. Inverts the processing actions. With the setting of `delete: apply`, when the `delete` action is run, the processing of this manifest will actually call the `apply` action. More on this flow control later in this document.                                                                                                          |
| `dependencies`     | Object          | Defines dependencies. See below for the full definition.                                                                                                                                                                                                                                                                                                                                           |

### Action Overrides

Action overrides is useful in some use cases where you need to make use of the `apply` logic of one extension in the case of a overall `delete` action.

When the `apply` action is requested when `py-animus` is run, it generally means that you want to _CREATE_ [resources](./01-what-is-a-resource.md). Therefore, the `delete` action means the opposite: you want to _DELETE_ resources.

However, by thinking about how extensions implement logic, it may be useful to leverage the `apply` extension logic during the `delete` action in some use cases. The are some use cases where this may be useful:

#### Use case: Run a `ShellScript` command to backup a directory during a `delete` action that will delete the directory

Consider the following example:

```yaml
---
kind: Project
version: v1
metadata:
  name: manage-my-example-dir
spec:
  loggingConfig: /path/this-manifest.yaml
  manifestFiles: 
  - /path/this-manifest.yaml
---
kind: StreamHandlerLogging
version: v1
metadata:
  name: StreamHandler
spec:
  level: debug
  loggingFormat: 'EXAMPLE: %(asctime)s %(levelname)s  %(message)s'
---
kind: ShellScript
version: v1
metadata:
  name: create-dir
  skipDeleteAll: true
spec:
  source:
    type: inline
    value: 'mkdir -p /path/to/dir'
---
kind: ShellScript
version: v1
metadata:
  name: backup-dir
  skipApplyAll: true
  actionOverrides:
    delete: apply
spec:
  source:
    type: inline
    value: 'rm -vf /backups/dir-backup.tar.gz ; tar czf /backups/dir-backup.tar.gz /path/to/dir'
---
kind: ShellScript
version: v1
metadata:
  name: delete-dir
  skipApplyAll: true
  actionOverrides:
    delete: apply
  dependencies:
    delete:
    - backup-dir
spec:
  source:
    type: inline
    value: 'rm -frR /path/to/dir'
```

In this example, during the `apply` action, _ONLY_ the manifest named `create-dir` will be processed, since the other manifests have the `skipApplyAll` field set to `true`.

But, when the `delete` action is called, the `create-dir` manifest processing will be skipped and then the `apply` actions will be called, _FIRST_ for the `backup-dir` and then for the `delete-dir` manifests.

A more practical implementation of this example is available [in this project repository](https://github.com/nicc777/py-animus/blob/main/examples/projects/simple-01/project-02.yaml).

On Unix-like operating systems, after [installing](../01-quick-start/01-installing.md) `py-animus`, you can run and test the example using the following commands:

```shell
# Run the apply action (IMPORTANT: Assuming you are running from a virtual environment !!!)
venv/bin/animus apply https://raw.githubusercontent.com/nicc777/py-animus/main/examples/projects/simple-01/project-02.yaml manage-my-example-dir default

# Create some files:
echo "content" > /tmp/project-02-example/file1
echo "more content" > /tmp/project-02-example/file2

# Some output will now be created. Check that the directory exist:
ls -lahrt /tmp/project-02-example

# Run the delete action (IMPORTANT: Assuming you are running from a virtual environment !!!)
venv/bin/animus delete https://raw.githubusercontent.com/nicc777/py-animus/main/examples/projects/simple-01/project-02.yaml manage-my-example-dir default

# Verify the directory and it's content is removed:
ls -lahrt /tmp/project-02-example

# Verify the backup has been made:
tar tvzf /tmp/dir-backup.tar.gz
```

The output from the last command should be something like the following:

```text
drwxrwxr-x nicc777/nicc777   0 2023-10-24 06:39 tmp/project-02-example/
-rw-rw-r-- nicc777/nicc777   8 2023-10-24 06:39 tmp/project-02-example/file1
-rw-rw-r-- nicc777/nicc777  13 2023-10-24 06:39 tmp/project-02-example/file2
```

### Dependencies

Assuming you have run the example of the previous section, you may have noticed the following log outputs during the `apply` and `delete` actions:

```shell
# APPLY ACTION OUTPUT
STARTUP: Setting Default Logging Handler: "StreamHandler"
STARTUP: Initial global logging level: INFO
[ animus.py:run_main:15 ] INFO - Starting
[ __init__.py:initialize_animus:15 ] INFO - Init Start
[ __init__.py:initialize_animus:46 ] INFO -    Init Done
[ manifest_processing.py:process_project:204 ] INFO - Project "manage-my-example-dir" selected for processing
EXAMPLE: 2023-10-24 07:04:53,656 INFO  Logging ready
EXAMPLE: 2023-10-24 07:04:53,734 INFO  Project "manage-my-example-dir" Execution Plan: {'apply': ['create-dir'], 'delete': ['backup-dir', 'delete-dir']}
EXAMPLE: 2023-10-24 07:04:53,734 INFO  APPLYING "create-dir"
EXAMPLE: 2023-10-24 07:04:53,734 INFO  [ShellScript:create-dir:v1] Registered action "Run ShellScript" with status "APPLY_PENDING"
EXAMPLE: 2023-10-24 07:04:53,734 INFO  [ShellScript:create-dir:v1] APPLY CALLED
EXAMPLE: 2023-10-24 07:04:53,738 INFO  [ShellScript:create-dir:v1] Return Code: 0
EXAMPLE: 2023-10-24 07:04:53,739 INFO  Project Applied
EXAMPLE: 2023-10-24 07:04:53,739 INFO  ANIMUS DONE



# DELETE ACTION OUTPUT
STARTUP: Setting Default Logging Handler: "StreamHandler"
STARTUP: Initial global logging level: INFO
[ animus.py:run_main:15 ] INFO - Starting
[ __init__.py:initialize_animus:15 ] INFO - Init Start
[ __init__.py:initialize_animus:46 ] INFO -    Init Done
[ manifest_processing.py:process_project:204 ] INFO - Project "manage-my-example-dir" selected for processing
EXAMPLE: 2023-10-24 07:05:11,360 INFO  Logging ready
EXAMPLE: 2023-10-24 07:05:11,443 INFO  Project "manage-my-example-dir" Execution Plan: {'apply': ['create-dir'], 'delete': ['backup-dir', 'delete-dir']}
EXAMPLE: 2023-10-24 07:05:11,443 INFO  [ShellScript:backup-dir:v1] Registered action "Run ShellScript" with status "DELETE_PENDING"
EXAMPLE: 2023-10-24 07:05:11,443 WARNING  Delete action for "backup-dir" was rerouted to Apply action...
EXAMPLE: 2023-10-24 07:05:11,443 INFO  APPLYING "backup-dir"
EXAMPLE: 2023-10-24 07:05:11,443 INFO  [ShellScript:backup-dir:v1] Registered action "Run ShellScript" with status "APPLY_PENDING"
EXAMPLE: 2023-10-24 07:05:11,443 INFO  [ShellScript:backup-dir:v1] APPLY CALLED
EXAMPLE: 2023-10-24 07:05:11,450 INFO  [ShellScript:backup-dir:v1] Return Code: 0
EXAMPLE: 2023-10-24 07:05:11,451 INFO  [ShellScript:delete-dir:v1] Registered action "Run ShellScript" with status "DELETE_PENDING"
EXAMPLE: 2023-10-24 07:05:11,451 WARNING  Delete action for "delete-dir" was rerouted to Apply action...
EXAMPLE: 2023-10-24 07:05:11,451 INFO  APPLYING "delete-dir"
EXAMPLE: 2023-10-24 07:05:11,451 INFO  [ShellScript:delete-dir:v1] Registered action "Run ShellScript" with status "APPLY_PENDING"
EXAMPLE: 2023-10-24 07:05:11,451 INFO  [ShellScript:delete-dir:v1] APPLY CALLED
EXAMPLE: 2023-10-24 07:05:11,454 INFO  [ShellScript:delete-dir:v1] Return Code: 0
EXAMPLE: 2023-10-24 07:05:11,455 INFO  Project Deleted
EXAMPLE: 2023-10-24 07:05:11,455 INFO  ANIMUS DONE
```

Of note here is the line with the text `Execution Plan` - usually around the 8th line (with INFO level logging). With the `apply` action, there is effectively only ONE action to process, since the other two are excluded by the `skipApplyAll` setting. During the `delete` action, there are two actions to perform, and the `backup-dir` will always be processed before `delete-dir` because the latter has a dependency on `backup-dir`.

## Spec Fields

Fields in this section are highly dependant on the implementation of each extension.

The `py-animus` project ships with a minimal set of "standard" extensions that is [documented here](../03-standard-extensions-documentation/README.md).

To learn more how to use third party extensions or how to  create your own extensions, refer to [this section](../04-third-party-extensions/README.md).

# Special Manifests

There are a number of manifest kinds that are supplementary and not directly related to the actual IaC process. These are:

| Manifest Category     | Kind(s)                                                                                                                         | Required | Purpose                                                                                                                                              |
|-----------------------|---------------------------------------------------------------------------------------------------------------------------------|:--------:|------------------------------------------------------------------------------------------------------------------------------------------------------|
| Project Definition    | `Project`                                                                                                                       | Yes      | At least ONE project is required to define the various other manifests to include in this project. Projects can have dependencies on other projects. |
| Logging Configuration | `StreamHandlerLogging`, `SyslogHandlerLogging`, `DatagramHandlerLogging`, `FileHandlerLogging` and `RotatingFileHandlerLogging` | No       | Define the logging when processing the project(s)                                                                                                    |
| Values                | `Values`                                                                                                                        | No       | Values can be defined per environment to accommodate slightly different configurations depending on the environment target for the deployment.       |

# Project(s)

A project forms the bases of a group of manifests that should be processed together. A project also allows to group related resources to manage together and through the ability to define project dependencies, there are even more options to build a hierarchy to groups of resources that should be processed in an order.

## Project Dependencies

WHen processing the project manifests, dependencies are only processed from the initial referenced project and it's dependencies. Tak the following example:

```text
+-----------+   +-----------+   +-----------+
|           |   |           |   |           |
| Project A +-->+ Project B +-->+ Project C +
|           |   |           |   |           |
+-----------+   +-----------+   +-----------+
```

Project has a dependency on Project B, and project B has a dependency on Project C. If the initial project starting reference is A, the processing order will be C, then B then A. If the starting reference is project B, project C will be processed first, the B and Project A will not be processed at all. Finally, if the starting reference is Project C, only project C will be processed.

Keep in mind that with "_processing_" the goal is to ensure a [desired state](./02-what-is-desired-state.md) as defined in the manifests for each project. Changes in the configuration will therefore lead to those changes be applied to the targeted resources in order to achieve the desired state.

## Project Spec

The following fields are available in the Project `spec`:

| Field              | Type            | Required | Default Value                          | Description                                                                                                                                                               |
|--------------------|-----------------|:--------:|----------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `workDirectory`    | String          | No       | Calculated at runtime                  | A temporary directory on the local file system that can be used to store files.                                                                                           |
| `loggingConfig`    | String          | No       | Built in logging configuration is used | Control over what kind of logging can be used and where to send logs as well as the message format.                                                                       |
| `valuesConfig`     | List of Strings | No       | None (No Values)                       | Define the files where values are defined.                                                                                                                                |
| `extensionPaths`   | List of Strings | No       | None (No Extensions)                   | Define the files where third party extensions are defined (source files for extension processing).                                                                        |
| `manifestFiles`    | List of Strings | Yes      | N/A                                    | At least ONE source file is required that includes actual manifests to process.                                                                                           |
| `skipConfirmation` | Boolean         | No       | False                                  | If set to `True`, confirmation to continue will not be required. The default value is `False` and therefore each new run will require user input to confirm to proceed.   |

Notes about file references:

* A "file" can be a path to a local file on the system, OR a web URL
* All manifests can be defined in ONE file, which will then result in all the various configuration options pointing to the same file - as in [example 1](../../../examples/projects/simple-01/project-01.yaml) and [example 2](../../../examples/projects/simple-01/project-02.yaml).

# See Also

* [What is a resource](./01-what-is-a-resource.md)
* [What is a "_Desired State_"](./02-what-is-desired-state.md)
* [Defining desired resource state in a Manifest](./03-defining-desired-resource-state-in-a-manifest.md)
* [Actions that can be performed to enforce resource state](./04-actions-that-can-be-performed-to-enforce-resource-state.md)
* [Extensions for every resources](./05-extensions-for-every-resources.md)
* [How to think of Environments](./06-environments.md)
* [How to use Values](./07-values.md)
* [Using Variables](./08-variables.md)
* [Planning and Project Hierarchy, Dependencies and Other Consideration](./09-planning-and-hierarchy.md)

<hr />

Quick Navigation: [Documentation home](../../../README.md) | [Up](./README.md)