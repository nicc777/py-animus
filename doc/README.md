# PyAnimus Documentation

The documentation focus on two parts:

* The implementation of classes that extend `ManifestBase`
* How to work with the `ManifestManager` and roll your own solution

# Basic Concepts

More people are getting familiar with [Kubernetes style Manifest files](https://kubernetes.io/docs/reference/glossary/?all=true#term-manifest).

This solution allows users to create application logic that can implement the state as specified by a manifest file.

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

export DEBUG=1

docker run --rm -e "DEBUG=1" \
  -v $PWD/examples/hello-world/src:/tmp/src \
  -v $PWD/examples/hello-world/manifest:/tmp/data \
  -v /tmp/results:/tmp/hello-world-result \
  animus -m /tmp/data/hello-v1.yaml -s /tmp/src
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

> **Warning**
> Keep in mind the manifest always contains the desired state. Therefore, in this example, the implementation will ensure that the specified file always contain the text as specified in the manifest.


