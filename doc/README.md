
- [py\_animus Documentation](#py_animus-documentation)
- [Basic Concepts](#basic-concepts)
  - [Manifests and Handler Classes for Manifests](#manifests-and-handler-classes-for-manifests)
  - [The Classes Implementing the Manifest](#the-classes-implementing-the-manifest)
    - [The `__init__` method](#the-__init__-method)
    - [The `implemented_manifest_differ_from_this_manifest` method](#the-implemented_manifest_differ_from_this_manifest-method)
    - [The `apply_manifest` method](#the-apply_manifest-method)
    - [The `delete_manifest` method](#the-delete_manifest-method)
  - [The `Variable` base class and `VariableCache`](#the-variable-base-class-and-variablecache)
    - [How data is passed around](#how-data-is-passed-around)
    - [Basic Workflow](#basic-workflow)
  - [Orchestration through the `ManifestManager`](#orchestration-through-the-manifestmanager)

# py_animus Documentation

The documentation focus on two parts:

* The implementation of classes that extend `ManifestBase`
* How to work with the `ManifestManager` and roll your own solution (TODO)

# Basic Concepts

## Manifests and Handler Classes for Manifests

More people are getting familiar with [Kubernetes style Manifest files](https://kubernetes.io/docs/reference/glossary/?all=true#term-manifest).

Thr `animus` solution allows users to create application logic that can implement the state as specified by a manifest file, where each manifest is tied to a specific class implementing by linking the `kind` to an actual class that implements the desired state as defined in the manifest.

> **Note**
> Keep in mind the manifest always contains the desired state. 

Take an example manifest like the following:

```yaml
---
kind: HelloWorld
version: v1
metadata:
  name: hello-world
spec:
  file: /tmp/hello-world-result/output.txt
  content: |
    This is the contents of the file
    specified in the file property of
    the spec.   
```

> **Note**
> An example is provided. The file above is from `examples/hello-world/manifest/hello-v1.yaml`.

The application will expect some implementation of `ManifestBase` that is called `HelloWorld`. You can have a look at the file `examples/hello-world/src/hello-v1.py` for an example.

Using the docker version of this application, on a *nix host you can try out the example with the following commands:

```shell
// Assuming we are running from the cloned project path...

mkdir /tmp/results

rm -frR /tmp/results/*

docker run --rm -e "DEBUG=1" \
  -v $PWD/examples/hello-world/src:/tmp/src \
  -v $PWD/examples/hello-world/manifest:/tmp/data \
  -v /tmp/results:/tmp/hello-world-result \
  ghcr.io/nicc777/py-animus:release apply -m /tmp/data/hello-v1.yaml -s /tmp/src
```

You can run the exact same docker command a couple of times.

What happens?

On the FIRST run, the following will happen:

* Docker will create the various mount points where `/tmp/src` will contain our custom Python implementation, `/tmp/data` will contain the YAML manifest and the output will be stored in `/tmp/hello-world-result` which is on the local host filesystem located in `/tmp/results`, which should be empty on the first run.
* The application loads the custom source code and registers it in the `ManifestManager`
* Next, the application loads the YAML manifest and stores it in the `ManifestManager`
* Finally, the application loops through all the parsed manifest files and applied them to the appropriate custom implementation. The match is made by matching the `kind` (`HelloWorld`) in the manifest to an implementation defined in the `ManifestManager` which will be our class named `HelloWorld`
* In the `HelloWorld` class, we first check if the file already exists by making a call to the `implemented_manifest_differ_from_this_manifest()` method. Finally, the result is recorded in the `VariableCache`
* The application now loops through available variables in the `VariableCache` and dumps the values.
* The application exists

You can see the file created by issuing the following command:

```shell
cat /tmp/results/output.txt
```

If you edit either the file in `/tmp/results/output.txt` or the manifest, any next run will update the file contents again to align to what is defined in the manifest. 

> **Note**
> Keep in mind the manifest always contains the desired state. Therefore, in this example, the implementation will ensure that the specified file always contain the text as specified in the manifest.

## The Classes Implementing the Manifest

Whet the example is run, output on the terminal may look something like the following:

| Line #  | Log Level | Log Text                                                                                                                                                                                                                                                            |
|:-------:|:---------:|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 01 - 07 | INFO      | `Logging init done`                                                                                                                                                                                                                                                 |
| 08      | INFO      | `ok`                                                                                                                                                                                                                                                                |
| 09      | INFO      | `Returning CLI Argument Parser`                                                                                                                                                                                                                                     |
| 10      | DEBUG     | `Command line arguments parsed...`                                                                                                                                                                                                                                  |
| 11      | DEBUG     | `   parsed_args: Namespace(manifest_locations=[['/tmp/data/hello-v1.yaml']], src_locations=[['/tmp/src']])`                                                                                                                                                         |
| 12      | DEBUG     | `   unknown_args: []`                                                                                                                                                                                                                                               |
| 13      | DEBUG     | `Ingesting source file /tmp/src`                                                                                                                                                                                                                                    |
| 14      | INFO      | `Logging init done`                                                                                                                                                                                                                                                 |
| 15      | INFO      | `Registered manifest "HelloWorld" of version v1`                                                                                                                                                                                                                    |
| 16      | INFO      | `Registered classes: ['HelloWorld']`                                                                                                                                                                                                                                |
| 17      | DEBUG     | `configuration={'part_1': {'kind': 'HelloWorld', 'version': 'v1', 'metadata': {'name': 'hello-world'}, 'spec': {'file': '/tmp/hello-world-result/output.txt', 'content': 'This is the contents of the file\nspecified in the file property of\nthe spec.   \n'}}}`  |
| 18      | DEBUG     | `Applying manifest named "hello-world"`                                                                                                                                                                                                                             |
| 19      | INFO      | `[HelloWorld] Not yet applied. Applying "HelloWorld" named "hello-world"`                                                                                                                                                                                           |
| 20      | INFO      | `[Variable:HelloWorld:hello-world] NOT EXPIRED - TTL less than zero - expiry ignored`                                                                                                                                                                               |
| 21      | INFO      | `[Variable:HelloWorld:hello-world] Returning value`                                                                                                                                                                                                                 |
| 22      | INFO      | `RESULT: HelloWorld:hello-world=True`                                                                                                                                                                                                                               |

> **Note**
> Some logging details may change and may not reflect exactly as shown above. 

The interesting lines are the following:

* Line 13 - THe application now goes through the Python files in the directory `/tmp/src` and looks for classes to ingest
* Line 15 - A class called `HelloWorld` is registered in the `ManifestManager`
* Line 18 - Based on the `kind` defined in the Manifest, the `ManifestManager` will apply the manifest by calling the apply method of the registered `HelloWorld`
* Line 19 - From the `HelloWorld` class, we see that the manifest has not yet been applied, or the data is different (this implementation just checks if the output file exists or not and if it exists, the content is compared to the manifest supplied data)
* Line 22 - After the application completes it's run, all the current variables are dumped. In this case, there is only one variable

If the data in the newly created file is not changed and we run the exact same command again, we notice the following difference in the log messages: `[HelloWorld] Already Applied "HelloWorld" named "hello-world"` 

In the `HelloWorld` there are at least four methods to pay attention to.

### The `__init__` method

The init method is fairly standard for all classes:

```python
class HelloWorld(ManifestBase):

    def __init__(self, logger=get_logger(), post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)
```

The exact implementation may change in the near future (see [the road map](../TODO.md)), but at the moment, the `ManifestManager` only registers one version of a class, even if given multiple classes of the same name.

### The `implemented_manifest_differ_from_this_manifest` method

This method must implement logic to determine the following:

* If the manifest have not yet been applied, return `TRUE`
* If the manifest have previously been applied, but the implemented state is now different from the provided manifest `sped`, return `TRUE`
* If the manifest have previously been applied, and the implemented state is still matching the provided manifest `sped`, return `FALSE`

### The `apply_manifest` method

When an apply command is provided to the application, it will call this method.

The intent of this method is to implement logic that will create a state that satisfies the `spec` of the manifest.

### The `delete_manifest` method

When an delete command is provided to the application, it will call this method.

The intent of this method is to implement logic that will delete a current implementation and it may or may not depend on the `spec` of the manifest.

## The `Variable` base class and `VariableCache`

### How data is passed around

The `ManifestManager` class instance is generally responsible to orchestrate the applying of commands based on manifests file content and implementations of `ManifestBase`.

A part of this orchestrations deals with having some way to share data among all calls to various class instances. This is done via the `VariableCache` implementation that stores `Variable` instances which other processes can store and/or read as required.

Each time the `ManifestManager` calls a method in an implementation of `ManifestBase`, a reference to the `VariableCache` is passed as well, which will make all `Variable` instances available to query.

> **Warning**:
> There are no specific safeguards built into `VariableCache` and it is possible for an implementation of `ManifestBase` to override any value set in the `VariableCache`. Best practice is to only _read_ a `Variable` not "owned" or controlled by the specific implementation of `ManifestBase`

### Basic Workflow

When the `ManifestManager` is initialized, an instance of `VariableCache` is created. Only one copy of the `VariableCache` should ever exist.

As the `ManifestManager` calls an implementation of `ManifestBase`, to either the `apply_manifest()` or `delete_manifest()` methods, a reference of the `VariableCache` is passed in as a parameter named `variable_cache`.

The `apply_manifest()` and `delete_manifest()` methods can in turn also pass that reference internally to other methods, like `implemented_manifest_differ_from_this_manifest()` as required.

Any call to the `store_variable()` will either create a new instance of `Variable` to be stored or override an existing instance if the `overwrite_existing` parameter is True (default is False).

As the implementation of `ManifestBase` processes the call to the `apply_manifest()` and `delete_manifest()` methods, it can make calls to the `store_variable()` and `get_value()` methods as required.

A quick way to get the current references (names) of all stored `Variable` instances if needed can be done as follow:

```python
# Get the names
current_variable_names = tuple(variable_cache.values.keys())

# Iterate over every named variable:
for variable_name in tuple(variable_cache.values.keys()):
    current_value = variable_cache.get_value(variable_name=variable_name)
    # Do further processing on the returned value...
```

> **Warning**:
> Important to remember is that calls to the `VariableCache` methods `store_variable()` and `get_value()` could raise exceptions (depending on optional parameters set), and the implementation of `ManifestBase` should be able to handle that appropriately as required.

## Orchestration through the `ManifestManager`

TODO
