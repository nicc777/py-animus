
- [py\_animus Documentation](#py_animus-documentation)
- [Basic Concepts](#basic-concepts)
  - [Manifests and Handler Classes for Manifests](#manifests-and-handler-classes-for-manifests)
  - [The Classes Implementing the Manifest](#the-classes-implementing-the-manifest)
    - [The `__init__` method](#the-__init__-method)

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
kind: HelloWorldV1
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

The application will expect some implementation of `ManifestBase` that is called `HelloWorldV1`. You can have a look at the file `examples/hello-world/src/hello-v1.py` for an example.

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
* Finally, the application loops through all the parsed manifest files and applied them to the appropriate custom implementation. The match is made by matching the `kind` (`HelloWorldV1`) in the manifest to an implementation defined in the `ManifestManager` which will be our class named `HelloWorldV1`
* In the `HelloWorldV1` class, we first check if the file already exists by making a call to the `implemented_manifest_differ_from_this_manifest()` method. Finally, the result is recorded in the `VariableCache`
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
| 15      | INFO      | `Registered manifest "HelloWorldV1" of version v1`                                                                                                                                                                                                                    |
| 16      | INFO      | `Registered classes: ['HelloWorldV1']`                                                                                                                                                                                                                                |
| 17      | DEBUG     | `configuration={'part_1': {'kind': 'HelloWorldV1', 'version': 'v1', 'metadata': {'name': 'hello-world'}, 'spec': {'file': '/tmp/hello-world-result/output.txt', 'content': 'This is the contents of the file\nspecified in the file property of\nthe spec.   \n'}}}`  |
| 18      | DEBUG     | `Applying manifest named "hello-world"`                                                                                                                                                                                                                             |
| 19      | INFO      | `[HelloWorldV1] Not yet applied. Applying "HelloWorldV1" named "hello-world"`                                                                                                                                                                                           |
| 20      | INFO      | `[Variable:HelloWorldV1:hello-world] NOT EXPIRED - TTL less than zero - expiry ignored`                                                                                                                                                                               |
| 21      | INFO      | `[Variable:HelloWorldV1:hello-world] Returning value`                                                                                                                                                                                                                 |
| 22      | INFO      | `RESULT: HelloWorldV1:hello-world=True`                                                                                                                                                                                                                               |

> **Note**
> Some logging details may change and may not reflect exactly as shown above. 

The interesting lines are the following:

* Line 13 - THe application now goes through the Python files in the directory `/tmp/src` and looks for classes to ingest
* Line 15 - A class called `HelloWorldV1` is registered in the `ManifestManager`
* Line 18 - Based on the `kind` defined in the Manifest, the `ManifestManager` will apply the manifest by calling the apply method of the registered `HelloWorldV1`
* Line 19 - From the `HelloWorldV1` class, we see that the manifest has not yet been applied, or the data is different (this implementation just checks if the output file exists or not and if it exists, the content is compared to the manifest supplied data)
* Line 22 - After the application completes it's run, all the current variables are dumped. In this case, there is only one variable

If the data in the newly created file is not changed and we run the exact same command again, we notice the following difference in the log messages: `[HelloWorldV1] Already Applied "HelloWorldV1" named "hello-world"` 

In the `HelloWorldV1` there are at least four methods to pay attention to.

### The `__init__` method

The init method is fairly standard for all classes:

```python
class HelloWorldV1(ManifestBase):

    def __init__(self, logger=get_logger(), post_parsing_method: object=None, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)
```

In terms of best practices, it is good idea to add some version as part of the class name. The exact implementation may change in the near future (see [the road map](../TODO.md)), but at the moment, the `ManifestManager` only registers one version of a class, given multiple classes of the same name.

