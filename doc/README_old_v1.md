
- [py\_animus Documentation](#py_animus-documentation)
- [Terminology](#terminology)
- [Basic Concepts](#basic-concepts)
  - [Manifests and Handler Classes for Manifests](#manifests-and-handler-classes-for-manifests)
  - [The Classes Implementing the Manifest](#the-classes-implementing-the-manifest)
    - [The `__init__` method](#the-__init__-method)
    - [The `implemented_manifest_differ_from_this_manifest` method](#the-implemented_manifest_differ_from_this_manifest-method)
    - [The `apply_manifest` method](#the-apply_manifest-method)
    - [The `delete_manifest` method](#the-delete_manifest-method)
  - [The `Variable` base class and `VariableCache`](#the-variable-base-class-and-variablecache)
    - [How data is passed around](#how-data-is-passed-around)
    - [Basic Variable Workflow](#basic-variable-workflow)
- [More feature specific documentation](#more-feature-specific-documentation)

# py_animus Documentation

The documentation focus on two parts:

* The implementation of classes that extend `ManifestBase`
* How to work with the `ManifestManager` and roll your own solution (TODO)

# Terminology

| Term/Phrase                   | Meaning                                                                                                        |
|-------------------------------|----------------------------------------------------------------------------------------------------------------|
| Apply or Applying a Manifest  | The process of implementing procedures to achieve a desired state as defined in a manifest                     |
| Delete or Deleting a Manifest | The process of implementing procedures to delete artifacts created previously by an apply action               |
| Desired State                 | Could mean several things, but in general refers to some end-result that can be reliably verified through code |
| Manifest                      | A YAML file expressing a desired state                                                                         |
| Process or processing         | Similar to the concept of "implementing procedures" - basically executing code                                 |

# Basic Concepts

## Manifests and Handler Classes for Manifests

More people are getting familiar with [Kubernetes style Manifest files](https://kubernetes.io/docs/reference/glossary/?all=true#term-manifest).

Thr `animus` solution allows users to create application logic that can implement the state as specified by a manifest file, where each manifest is tied to a specific class implementing by linking the `kind` to an actual class that implements the desired state as defined in the manifest.

> **Note**
> Keep in mind the manifest always contains the desired state. 

The file `examples/linked-manifests/manifest/linked-v1.yaml` ([link](../examples/linked-manifests/manifest/linked-v1.yaml)) contains the example manifest to be used in this quick introduction.

_**Manifest Specification**_

| Field                              | Type    | Required | Description                                                                                                                                                                                                          |
|------------------------------------|:-------:|:--------:|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `kind`                             | String  | Yes      | Maps to the Class name that handles the processing of this manifest file.                                                                                                                                            |
| `version`                          | String  | Yes      | Some form of version is required. It helps with maintaining implementations of the same kind as systems evolve.                                                                                                      |
| `metadata.name`                    | String  | Yes      | A unique name. Any other manifest could have some reference to this manifest, and therefore the name must be unique at runtime across all ingested manifest files.                                                   |
| `metadata.skipApplyAll`            | Boolean | No       | When all manifests are applied, any manifest with this entry and a value of `true` will be skipped. Ideal for "child" manifests invoked by "parent" manifests as needed.                                             |
| `metadata.skipDeleteAll`           | Boolean | No       | When all manifests are deleted, any manifest with this entry and a value of `true` will be skipped. Ideal for "child" manifests invoked by "parent" manifests as needed.                                             |
| `metadata.dependencies.apply`      | List    | No       | Contains a list of names pointing to manifests with the name in their `metadata.name` fields that must be applied before applying this manifest.                                                                     |
| `metadata.dependencies.delete`     | List    | No       | Contains a list of names pointing to manifests with the name in their `metadata.name` fields that must be deleted before deleting this manifest.                                                                     |
| `metadata.executeOnlyOnceOnApply`  | Boolean | No       | If set to True, ensure that the `ManifestBase` implementation method `apply_manifest()` is called only once. Default is `false` meaning the method may be called multiple times depending on dependency references.  |
| `metadata.executeOnlyOnceOnDelete` | Boolean | No       | If set to True, ensure that the `ManifestBase` implementation method `delete_manifest()` is called only once. Default is `false` meaning the method may be called multiple times depending on dependency references. |
| `metadata.environments`            | List    | No       | Default is one environment called `default`. List the environment names for which this manifest applies.                                                                                                             |
| `spec.<dict>`                      | Dict    | Yes      | The intent is that the `spec` contains the data required for processing the manifest file by the implementation class for this version of the manifest.                                                              |

_**Manifest General Rules**_

* Field names must be lower case (they will be converted during parsing to lower case, if not)
* The `metadata.name` field is unique, even across different versions of a manifest. For example, `kind: Example` of `version: 1` must have a different name than `kind: Example` of `version: 2`
* Any manifest listed under dependencies will be processed first before the current manifest is processed.
* To safeguard against potential hidden circular references, each manifest processed as a dependency of another will have their executions counted and if the count exceeds a certain threshold, the `ManifestManager` will throw an exception. This behavior can be controlled in the following ways:
    * Set an environment variable `MAX_CALLS_TO_MANIFEST` with a number. The default value is 10, meaning that any manifest will have the `apply_manifest()` or `delete_manifest()` methods called a maximum of 10 times before an exception is thrown.
    * Set the `metadata.executeOnlyOnceOnApply` or `metadata.executeOnlyOnceOnDelete` in the manifest to ensure the `apply_manifest()` or `delete_manifest()` methods is only ever called once, regardless of how many times the manifest is referenced. The test for `MAX_CALLS_TO_MANIFEST` will still be evaluated to detect potential circular references even though the actual call to the various methods will only ever occur once. 

> **Warning**
> The `metadata.executeOnlyOnceOnApply` or `metadata.executeOnlyOnceOnDelete` settings are only evaluated in the `ManifestManager` and if a `ManifestBase` implementation makes a call using the `manifest_lookup_function` function reference, these values will have no effect unless also considered in the `ManifestBase` implementation

The application will expect some implementation of `ManifestBase` that is called `HelloWorld`. You can have a look at the file `examples/hello-world/src/hello-v1.py` for an example.

Using the docker version of this application, on a *nix host you can try out the example with the following commands:

```shell
# Assuming we are running from the cloned project path...
# Also assuming you are running on a *nix like system

mkdir /tmp/results

rm -frR /tmp/results/*

docker run --rm -e "DEBUG=0" \
  -v $PWD/examples/linked-manifests/src:/tmp/src \
  -v $PWD/examples/linked-manifests/manifest:/tmp/data \
  -v /tmp/results:/tmp/example-page-result \
  ghcr.io/nicc777/py-animus:latest apply -m /tmp/data/linked-v1.yaml -s /tmp/src
```

You can run the exact same docker command a couple of times.

What happens?

On the FIRST run, the following will happen:

* Docker will create the various mount points where `/tmp/src` will contain our custom Python implementation, `/tmp/data` will contain the YAML manifest and the output will be stored in `/tmp/example-page-result` which is on the local host filesystem located in `/tmp/results`, which should be empty on the first run.
* The application loads the custom source code and registers it in the `ManifestManager`
* Next, the application loads the YAML manifest and stores it in the `ManifestManager`
* Finally, the application loops through all the parsed manifest files and applied them to the appropriate custom implementation.

You can see the file created by issuing the following command:

```shell
cat /tmp/results/output.txt
```

If you edit either the file in `/tmp/results/output.txt` or the manifest, any next run will update the file contents again to align to what is defined in the manifest. 

> **Note**
> Keep in mind the manifest always contains the desired state. Also, in this example, the `WebsiteUpTest` is never processed on it's own and is only ever referred to by other manifests in their dependencies list, as needed.

To delete the downloaded file, just run the same docker command, but instead of `apply` use the `delete` command. The previously downloaded file should now be gone

## The Classes Implementing the Manifest

From the example, the source file `examples/linked-manifests/src/linked-v1.py` ([link](../examples/linked-manifests/src/linked-v1.py)) implements two classes that extend `ManifestBase`:

* `WebsiteUpTest`
* `DownloadWebPageContent`

When the manifests are applied, the logic is that first a check is done to see if the site is up and then the page is downloaded. When the downloaded content is "deleted", (delete action), there is no need to check if the site is up and therefore that check can be skipped.

The current workflow will try to apply all manifests, looping through the whole list of ingested manifest files and doing a lookup to see if an implementation is available that can apply that manifest. This is done in two phases:

1. The first phase reads all the source files (`*.py` from the `-s` command line parameter), which is stored in the `ManifestManager`
2. Next each of the manifest files are read (any file found in the directories pointed to by the `-m` command line parameter)

In this example, the `WebsiteUpTest` is a dependency of the `DownloadWebPageContent` manifest which only has to be processed on an "_apply_" action. Therefore, not the `metadata` section in the file `examples/linked-manifests/manifest/linked-v1.yaml` ([link](../examples/linked-manifests/manifest/linked-v1.yaml)). Note the following:

* Because the `WebsiteUpTest` manifest does not have to be processed every time, the `skipApplyAll` and `skipDeleteAll` is set to true.
* Because the `WebsiteUpTest` manifest has to be processed before the `DownloadWebPageContent` is processed, the latter contains a `metadata.dependencies.apply` dependency with the name of the `WebsiteUpTest` manifest

Therefore, when all the manifests are processed (via an _apply_ or _delete_ action), the `ManifestManager` will loop through all the manifests and retrieve their implementation class. Once an instance of that class is retrieved, the `skipApplyAll` and `skipDeleteAll` booleans are evaluated to see if processing for that instance must proceed. Finally, if the class must be processed, the `process_dependencies()` method of the class instance is called with the appropriate parameters set depending on the _apply_ or _delete_ action.

Next, a more detailed look at the anatomy of the classes that extend `ManifestBase`, specifically those methods the user needs to override.

### The `__init__` method

The init method is fairly standard for all classes:

```python
class DownloadWebPageContent(ManifestBase):

    def __init__(self, logger=get_logger(), post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)
```

Multiple versions of `DownloadWebPageContent` can exist, as long as they are in different source files.

### The `implemented_manifest_differ_from_this_manifest` method

This method must implement logic to determine the following:

* If the manifest have not yet been applied, return `TRUE`
* If the manifest have previously been applied, but the implemented state is now different from the provided manifest `spec`, return `TRUE`
* If the manifest have previously been applied, and the implemented state is still matching the provided manifest `spec`, return `FALSE`

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

### Basic Variable Workflow

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


# More feature specific documentation

The following documentation deep dives into the implementation of specific features:

| Feature                                                                 | Feature Description                                                                                                                                                                                                                                                                                                                                            |
|-------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [Support for Environment Scope](target_environments.md)                 | Allows to define the environment scopes for each manifest. For example, you may have "sandbox", "test" and "production" environments and certain manifests may only be scoped for certain of these  environment.                                                                                                                                               |
| [The concept of Placeholder Values in Manifests](placeholder_values.md) | Adds support for using special placeholders in manifest files where a different value may be required depending on the target environment. The environment and value map is defined in a separate values files. This is very similar to how [Helm values](https://helm.sh/docs/chart_best_practices/values/) work, but more basic and with no logic statement. |
