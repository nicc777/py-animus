
Quick Navigation: [Documentation home](../../README.md) | [Up](./README.md)

<hr />

- [Included Examples](#included-examples)
- [Most Basic Example (or the "Hello World" demonstration)](#most-basic-example-or-the-hello-world-demonstration)
  - [The Project](#the-project)
  - [Running the example](#running-the-example)
  - [Cleaning Up](#cleaning-up)
- [See Also](#see-also)


# Included Examples

Examples are included in this repository. The following examples are currently maintained for documentation purposes:

* [Simple Example 1](../../../examples/projects/simple-01/)
* [Simple Example 2](../../../examples/projects/simple-02/)
* [Clone Git Repository Example](../../../examples/projects/clone_extensions_repo/)
* [Interactive Example for Downloading a Web Resource](../../../examples/projects/download_web_page_supplied_by_user_input/)

# Most Basic Example (or the "Hello World" demonstration)

This example uses the log configuration feature to process the manifests and eventually print some basic information on STDOUT - almost like a [hello world](https://www.helloworld.org/) example, although this one is arguably a lot more verbose than traditional examples.

In our most basic example we will run a shell script (assuming we run on a Unix type OS) that will create a file on your system: `~/hello-world.txt`

The file must contain text similar to the following:

```text
Action: apply with logging level set to debug
```

> **note**
> The actual logging verbosity is controlled with the environment variable `DEBUG`. If you do not set this environment variable to `1`, only `INFO` level messages will be logged, even though the log level was set to `DEBUG` in the logging manifests. Or at least - this is the setting for environment `sandbox1`. For environment `sandbox2`, logging will only be on `INFO` level regardless of what the `DEBUG` environment variable is set to.

## The Project

The "_[Simple Example 1](../../../examples/projects/simple-01/)_" directory contains the most basic example contained within one file: [The Project File](../../../examples/projects/simple-01/project-01.yaml)

The starting point for Animus is the Project Manifest.

```yaml
kind: Project
version: v1
metadata:
  name: project-1
  environments:
  - sandbox1
  - sandbox2
spec:
  workDirectory: '/tmp/sample-01'
  loggingConfig: https://raw.githubusercontent.com/nicc777/py-animus/main/examples/projects/simple-01/project-01.yaml
  valuesConfig:
  - https://raw.githubusercontent.com/nicc777/py-animus/main/examples/projects/simple-01/project-01.yaml
  extensionPaths: []
  manifestFiles:
  - https://raw.githubusercontent.com/nicc777/py-animus/main/examples/projects/simple-01/project-01.yaml
  skipConfirmation: false   
```

The Project Manifest defines locations or values for the following:

| Concept                               | Description                                                                                                                                                                                                                         |
|---------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Environments                          | An environment can mean different things for different people. At it most basic level an environment is just a grouping. It could be a grouping of servers, or cloud accounts or what ever you decide it to be.                     |
| Work Directory (or working directory) | A directory on the local system used for working with artifacts.                                                                                                                                                                    |
| Log Configuration                     | Animus supports several log configurations also defined in YAML to allow for flexibility and control of where logs produced by the running of Animus are sent.                                                                      |
| Values Definition                     | Value placeholders in YAML manifests can be used to define different values for different environments for a particular property.                                                                                                   |
| Manifest Files                        | The YAML files containing manifests that Animus supports.                                                                                                                                                                           |

In this example, everything is contained in the same file and the values of many of the properties therefore point to the same resource. The resource (manifest) can be a path and file on the local file system or a URL to a yaml file on the web.

## Running the example

Assuming you have already [installed](../01-quick-start/01-installing.md) Animus, you can run the example with the following command:

```shell
$ animus apply https://raw.githubusercontent.com/nicc777/py-animus/main/examples/projects/simple-01/project-01.yaml project-1 sandbox1
STARTUP: Setting Default Logging Handler: "StreamHandler"
STARTUP: Initial global logging level: INFO
[ animus.py:run_main:15 ] INFO - Starting
[ __init__.py:initialize_animus:15 ] INFO - Init Start
[ __init__.py:initialize_animus:46 ] INFO -    Init Done
[ manifest_processing.py:process_project:204 ] INFO - Project "project-1" selected for processing
*** 2023-10-26 05:58:10,096 INFO - manifest_processing.py:_process_logging_sections:105 - Logging ready
*** 2023-10-26 05:58:10,233 INFO - manifest_processing.py:process_project:260 - Project "project-1" Execution Plan: {'apply': ['shell-script-v1-minimal'], 'delete': ['cleanup']}
*** 2023-10-26 05:58:10,233 INFO - project_v1.py:apply_manifest:183 - Project Apply Action Processed
========================================

Current Execution Plan
----------------------

    shell-script-v1-minimal

Process the above manifest names in the shown order? [N|y]: y
========================================
*** 2023-10-26 05:58:14,210 INFO - __init__.py:run:152 - APPLYING "shell-script-v1-minimal"
*** 2023-10-26 05:58:14,211 INFO - extensions.py:log:324 - [ShellScript:shell-script-v1-minimal:v1] Registered action "Run ShellScript" with status "APPLY_PENDING"
*** 2023-10-26 05:58:14,211 INFO - extensions.py:log:324 - [ShellScript:shell-script-v1-minimal:v1] APPLY CALLED
*** 2023-10-26 05:58:14,214 INFO - extensions.py:log:324 - [ShellScript:shell-script-v1-minimal:v1] Return Code: 0
*** 2023-10-26 05:58:14,214 INFO - animus.py:run_main:28 - ANIMUS DONE

# TEST:
$ cat ~/hello-world.txt
Action: apply with logging level set to debug
```

> **note**
> To see much more verbose logging, set the `DEBUG` environment variable to `1`

## Cleaning Up

Running the cleanup:

```shell
$ animus delete https://raw.githubusercontent.com/nicc777/py-animus/main/examples/projects/simple-01/project-01.yaml project-1 sandbox1
STARTUP: Setting Default Logging Handler: "StreamHandler"
STARTUP: Initial global logging level: INFO
[ animus.py:run_main:15 ] INFO - Starting
[ __init__.py:initialize_animus:15 ] INFO - Init Start
[ __init__.py:initialize_animus:46 ] INFO -    Init Done
[ manifest_processing.py:process_project:204 ] INFO - Project "project-1" selected for processing
*** 2023-10-26 05:58:52,345 INFO - manifest_processing.py:_process_logging_sections:105 - Logging ready
*** 2023-10-26 05:58:52,432 INFO - manifest_processing.py:process_project:260 - Project "project-1" Execution Plan: {'apply': ['shell-script-v1-minimal'], 'delete': ['cleanup']}
*** 2023-10-26 05:58:52,433 INFO - project_v1.py:delete_manifest:190 - Project Delete Action Processed
========================================

Current Execution Plan
----------------------

    cleanup

Process the above manifest names in the shown order? [N|y]: y
========================================
*** 2023-10-26 05:58:54,375 INFO - extensions.py:log:324 - [ShellScript:cleanup:v1] Registered action "Run ShellScript" with status "DELETE_PENDING"
*** 2023-10-26 05:58:54,375 WARNING - __init__.py:run:172 - Delete action for "cleanup" was rerouted to Apply action...
*** 2023-10-26 05:58:54,375 INFO - __init__.py:run:152 - APPLYING "cleanup"
*** 2023-10-26 05:58:54,375 INFO - extensions.py:log:324 - [ShellScript:cleanup:v1] Registered action "Run ShellScript" with status "APPLY_PENDING"
*** 2023-10-26 05:58:54,375 INFO - extensions.py:log:324 - [ShellScript:cleanup:v1] APPLY CALLED
*** 2023-10-26 05:58:54,379 INFO - extensions.py:log:324 - [ShellScript:cleanup:v1] Return Code: 0
*** 2023-10-26 05:58:54,380 INFO - animus.py:run_main:28 - ANIMUS DONE

# TEST
$ cat ~/hello-world.txt
cat: /home/nicc777/hello-world.txt: No such file or directory
```

# See Also

* [Installing](./01-installing.md) `py-animus`
* [Command Line Arguments](./03-command-line-args.md)

<hr />

Quick Navigation: [Documentation home](../../README.md) | [Up](./README.md)