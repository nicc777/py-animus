# Features and other enhancements on the road map

> **Note**
> If you have an idea for the road map, pleas [open a new issue](https://github.com/nicc777/py-animus/issues/new?assignees=&labels=&template=enhancement.md&title=)

* [ ] Handle multiple versions of the same class in `ManifestManager`
* [ ] Add `metadata` field `skipApplyAll` (boolean value) to indicate to the `apply_command()` function in `src/py_animus/py_animus.py` if this manifest must be applied or not. A Value of `true` will skip over the manifest onto the next manifest
* [ ] Add `metadata` field `applyOrderSequence` (integer value) to indicate to the `apply_command()` function in `src/py_animus/py_animus.py` if this manifest has to be applied in a certain order. Manifests with this field will be considered first, and applied from low to high numbers. Manifests with the same integer value will be processed in more-or-less random order. Manifests without this field will be processed afterwards in more-or-less random order.
* [ ] Implement a roll back method called `rollback` in `ManifestBase` for a user to implement roll back logic. A roll back must be done on every manifest, in reverse order of applying/deleting, in case some error occurs. In addition, some additional `metadata` fields will be required in the manifest to guide the roll back processing. These include: a) `ignoreRollback` (boolean) which, if `true`, will not execute the roll back for this manifest in the event of an error
* [ ] Introduce a `ActionFailException` class which implementations of `ManifestBase` must raise when an apply/delete actions fails
* [ ] Introduce a `RollbackFailException` class which implementations of `ManifestBase` must raise when a roll back actions fails
* [ ] Add a command line parameter `--on-error` which can have values of either `rollback` (default) or `halt`. If the value is rollback, and any manifest apply/delete command fails, the application will run through the previously applied manifests in reverse order and call the `rollback` method of each. If the value is `halt`, the application will simply stop at the point where a apply/delete action of a manifest fails. Failure of an apply/delete action must be done via a `ActionFailException`
* [ ] Add a command line parameter `--report` which takes a directory name where a post apply/delete report will be generated. The default report will be done in MarkDown format. 
* [ ] Add a command line parameter `--report-html` which, if present, will convert the MarkDown report to HTML (see https://python-markdown.github.io/)
