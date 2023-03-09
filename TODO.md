# Features and other enhancements on the road map

> **Note**
> If you have an idea for the road map, pleas [open a new issue](https://github.com/nicc777/py-animus/issues/new?assignees=&labels=&template=enhancement.md&title=)

> **Note**
> A checkmark below would mean an Issue was created. For details and progress of the feature, refer to the issue itself.

# Version 1 Enhancements Road Map

* [x] Handle multiple versions of the same class in `ManifestManager` ([Issue 7](https://github.com/nicc777/py-animus/issues/7))
* [x] Add `metadata` field `skipApplyAll` (boolean value) to indicate to the `apply_command()` function in `src/py_animus/py_animus.py` if this manifest must be applied or not. A Value of `true` will skip over the manifest onto the next manifest. This will allow some manifests (children) to act as additional config for other manifests (parents). A parent is then responsible for "applying" the child manifest and consume the result via the variable(s) that was set. Typical use case would be a child manifest that defines/creates a login session which the parent manifest can use, for example to upload an artifact to a remote system. ([Issue 8](https://github.com/nicc777/py-animus/issues/8))
* [x] Add `metadata` field `applyOrderSequence` (integer value) to indicate to the `apply_command()` function in `src/py_animus/py_animus.py` if this manifest has to be applied in a certain order. Manifests with this field will be considered first, and applied from low to high numbers. Manifests with the same integer value will be processed in more-or-less random order. Manifests without this field will be processed afterwards in more-or-less random order. The `delete_command()` will operate in the reverse order. If a manifest has the `skipApplyAll` value set to `true`, the additional `applyOrderSequence` will have no effect, regardless of it's value. ([Issue 9](https://github.com/nicc777/py-animus/issues/9))
* [x] Add logic in `ManifestManager.get_manifest_instance_by_name()` to also support version consideration when looking up a `ManifestBase` implementation. Pass the YAML manifest version when applying or deleting a manifest. (depends on [Issue 7](https://github.com/nicc777/py-animus/issues/7))
* [x] Detect circular referenced dependencies 
* [x] Add a delete variable method to `VariableCache`

# Version 2 Features

> **Note**
> Focus for version 2 is on roll back and reporting. Part of rollback will be the basic ability to persist checksums of previous command results

* [ ] Create a base class `StatePersistance` that can store state and retrieve previously stored state. The `implemented_manifest_differ_from_this_manifest()` manifest in `ManifestBase` should be able to also make calls to an instance of this class to help determine if the current manifest differs from the running implementation.
* [ ] Introduce a `ActionFailException` class which implementations of `ManifestBase` must raise when an apply/delete actions fails
* [ ] Introduce a `RollbackFailException` class which implementations of `ManifestBase` must raise when a roll back actions fails
* [ ] Implement a roll back method called `rollback` in `ManifestBase` for a user to implement roll back logic. A roll back must be done on every manifest, in reverse order of applying/deleting, in case some error occurs. In addition, some additional `metadata` fields will be required in the manifest to guide the roll back processing. These include: a) `ignoreRollback` (boolean) which, if `true`, will not execute the roll back for this manifest in the event of an error
* [ ] Add a command line parameter `--on-error` which can have values of either `rollback` (default) or `halt`. If the value is rollback, and any manifest apply/delete command fails, the application will run through the previously applied manifests in reverse order and call the `rollback` method of each. If the value is `halt`, the application will simply stop at the point where a apply/delete action of a manifest fails. Failure of an apply/delete action must be done via a `ActionFailException`
* [ ] Add a command line parameter `--report` which takes a directory name where a post apply/delete report will be generated. The default report will be done in MarkDown format. 
* [ ] Add a command line parameter `--report-html` which, if present, will convert the MarkDown report to HTML (see https://python-markdown.github.io/)
* [ ] Produce an execution plan/graph given a set of manifests for a particular action. Use the DOT Language from [Graphviz](https://www.graphviz.org/)
