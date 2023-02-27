# py_animus

> `animus` as in a sense of purpose and reason

A python based plugable and extensible manifest processing system

The general idea is to create an extensible system that would be responsible for processing YAML Manifest files (similar to Kubernetes) in a consistent way.

Any Manifest file has the following top-level attribute names:

* `kind`
* `apiVersion`
* `metadata`
* `spec`

The goal is to implement classes that can process any `kind` of manifest of a specific version (or range of versions).

Processing a class means essentially to take the `metadata` and `spec` sub-attributes into consideration to ensure the stated configuration is applied during processing.

Processing must ensure that the desired end-state of the manifest can be implemented by user-defined logic.

Overall the system needs to be able to derive the implemented state versus the desired state in order to calculate and implement changes required to reach a desired state as defined in the manifest.

If this sounds very familiar, then yes - it is basically how Kubernetes work. The difference is that this library is not Kubernetes specific and aims to be more generalized methods that could be employed by potentially any system that must be continuously monitored and updated to fit a desired state.

[Documentation](https://github.com/nicc777/py-animus/tree/main/doc)

> **Warning**
> I have labeled this software `BETA`, but keep in mind testing in the real world has been limited and there may be a number of enhancements or changes forthcoming. 


# Use

## Quick start using pre-built Docker Image

Pull the image:

```shell
docker pull ghcr.io/nicc777/py-animus:release
```

Use (as per the [hello world example](https://github.com/nicc777/py-animus/tree/main/doc)):

```shell
docker run --rm -e "DEBUG=1" \
  -v $PWD/examples/hello-world/src:/tmp/src \
  -v $PWD/examples/hello-world/manifest:/tmp/data \
  -v /tmp/results:/tmp/hello-world-result \
  ghcr.io/nicc777/py-animus:release -m /tmp/data/hello-v1.yaml -s /tmp/src
```

