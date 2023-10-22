
Quick Navigation: [Documentation home](../../README.md) | [Up](./README.md)

<hr />

- [Installing using Pip](#installing-using-pip)
- [Building from source](#building-from-source)
- [Supported Python Versions](#supported-python-versions)
- [Updating or Upgrading](#updating-or-upgrading)
- [See Also](#see-also)

# Installing using Pip

Simply use the following command:

```shell
pip install py-animus
```

# Building from source

A build script is included. The basic steps:

```shell
# Clone the repository
git clone https://github.com/nicc777/py-animus.git
cd py-animus

# Create a virtual environment
python3 -m venv venv
. venv/bin/activate

# Install the pre-requisites
pip3 install build PyYAML chardet GitPython requests

# Run the build script
./build.sh
```

You can now install the package from the `dict/` directory in any other environment, for example:

```shell
# IN ANOTHER TERMINAL
cd /some/path

# Create a virtual environment
python3 -m venv venv
. venv/bin/activate

# Install
pip3 install /path/to/py-animus/dist/py_animus-1.1.0.tar.gz 
```

> **note**
> The version may change in the future, therefore adjust to fit your needs.

# Supported Python Versions

The current version was developed on Python 3.10 and therefore the recommended versions is 3.10+.

Older versions of Python in the 3.x series may still work. Python 2 is not supported and will almost certainly not work.

# Updating or Upgrading

Simply run the upgrade through pip:

```shell
# Using the normal PyPi package:
pip3 install --upgrade py-animus

# Or, when using the custom build example:
pip3 install --upgrade /path/to/py-animus/dist/py_animus-1.1.0.tar.gz 
```

# See Also

* [First project and capability demonstration](./02-first-project-and-capability-demonstration.md)

<hr />

Quick Navigation: [Documentation home](../../README.md) | [Up](./README.md)