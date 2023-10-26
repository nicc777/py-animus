# Features and other enhancements on the road map

> **Note**
> If you have an idea for the road map, pleas [open a new issue](https://github.com/nicc777/py-animus/issues/new?assignees=&labels=&template=enhancement.md&title=)

# Current tasks

* [ ] It seems there is a bug where spec field values is converted to strings (always) - check file `src/py_animus/helpers/manifest_processing.py` where we process `skipConfirmation`

# More testing to be done

Adapt tests in `tests/test_main.py` to accommodate for the CLI input now required (currently these tests "stall" because it is waiting for user input.)

# Documentation

Consider using something like [mkdocs](https://squidfunk.github.io/mkdocs-material/getting-started/) with a good theme to make documentation. 

