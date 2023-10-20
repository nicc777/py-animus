
- [Included Examples](#included-examples)
- [Most Basic Example (or the "Hello World" demonstration)](#most-basic-example-or-the-hello-world-demonstration)
  - [The Project](#the-project)
  - [Running the example](#running-the-example)
  - [Cleaning Up](#cleaning-up)
- [Other Examples](#other-examples)
- [Final Notes](#final-notes)


# Included Examples

Examples are included in this repository. The following examples are currently maintained for documentation purposes:

* [Simple Example 1](../../../examples/projects/simple-01/)
* [Simple Example 2](../../../examples/projects/simple-02/)
* [Clone Git Repository Example](../../../examples/projects/clone_extensions_repo/)
* [Interactive Example for Downloading a Web Resource](../../../examples/projects/download_web_page_supplied_by_user_input/)

# Most Basic Example (or the "Hello World" demonstration)

This example uses the log configuration feature to process the manifests and eventually print some basic information on STDOUT - almost like a [hello world](https://www.helloworld.org/) example, although this one is arguably a lot more verbose than traditional examples.

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

```

## Cleaning Up

TODO

# Other Examples

TODO

# Final Notes


