# PyAnimus Documentation

The documentation focus on two parts:

* The implementation of classes that extend `ManifestBase`
* How to work with the `ManifestManager` and roll your own solution

# Basic Concepts

More people are getting familiar with [Kubernetes style Manifest files](https://kubernetes.io/docs/reference/glossary/?all=true#term-manifest).

This solution allows users to create application logic that can implement the state as specified by a manifest file.

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

export DEBUG=1

docker run --rm -e "DEBUG=1" \
  -v $PWD/examples/hello-world/src:/tmp/src \
  -v $PWD/examples/hello-world/manifest:/tmp/data \
  -v /tmp/results:/tmp/hello-world-result \
  animus -m /tmp/data/hello-v1.yaml -s /tmp/src
```


