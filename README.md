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

[Documentation](doc/README.md)
