# py_animus

> `animus` as in a sense of purpose and reason

A python based plugable and extensible manifest processing system

The general idea is to create an extensible system that would be responsible for processing YAML Manifest files (similar to Kubernetes) in a consistent way to ensure the desired state as described in these files can be achieved.

# Why use this solution

The project was created as a result of finding a better way to manage environments with a mixture of deployment technologies including AWS CloudFormation and Terraform.

This project is not a replacement of any of these technologies but rather a wrapper of sorts that can use any number of existing deployments systems in any number of on-premise or public cloud scenarios.

More specifically, this project includes the base classes and basic processing and will rely on other projects to provide the detailed implementation logic for systems like AWS CloudFormation and Terraform.

> **Note**
> Imagine you have a mixed on-premise environment where you have some infrastructure as code in shell scripts and Terraform and you also have several public cloud accounts, each with their own tooling for deploying infrastructure as code. Now imagine you have complex applications that need to provision resources in multiple of these environments when deployed. How to you coordinate and orchestrate something like that? Existing tools like Terraform and others could be used. This implementation is a Python based approach to this problem and does not replace any of your existing tooling, but merely helps you bind it all together to perform some really complex orchestration.

Although the initial focus was on Infrastructure, it could very well be used in many other types of scenarios, including:

* Provisioning of public cloud accounts in a bootstrapping type scenario
* Deploying a mixture of Kubernetes based applications where some may use Helm and others using other technologies and/or package management solution.

Advantages of this system or approach:

* None of your existing tooling have to be replaced and often no additional modifications are required
* This tool can assist in orchestration of several existing tools to accomplish a single goal, for example the provisioning of infrastructure to support the deployment of an application
* This tool has no knowledge of anything, and all logic to process any manifest needs to be provided as Python code. In the future there will hopefully be a growing library of manifest processing implementations that support a growing number of environments and tools
* Implementation classes can be versioned and can be tied to specific versions of a manifest. In a real life scenario you could maintain various versions of implementation logic and manifests along side each other.
* A built in manifest dependency reference system allows you to dictate which manifests depend on which other manifests. The system will determine from this the order in which manifests needs to be applied
* The solution provides a class to store various variables that are shared and usable among all manifest implementations. Therefore, some context derived in the processing of one manifest can be stored and made available for consuming while processing other manifest implementations.
* The logic for applying and deleting manifest state is provided and in future releases also rollback and other features will be supported
* A basic command line tool is provided, as well as a containerized version of the command line tool. Just point to the class sources and the manifests and the system will process and implement state as defined and implemented.
* Apart from the command line tool, it is also possible to have full control over the processing of manifests, as all classes can be extended as required. You can therefore roll your own unique version of the command line tools.

![what is animus](images/animus.drawio.png)

# The Manifest File

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
> I no longer consider this to be `beta` software, but real life usage is still limited. Therefore note that there may still be bugs. Please log all bugs as an [issue](https://github.com/nicc777/py-animus/issues).

# Quick Intro Usage

## Installation

This project is also hosted on https://pypi.org/project/py-animus/

Installation:

```shell
pip install py-animus
```

> **Note**
> It is always a good idea to use [Python Virtual environments](https://docs.python.org/3/tutorial/venv.html) and I encourage it as well.

## Using pre-built Docker Image

Pull the image:

```shell
docker pull ghcr.io/nicc777/py-animus:latest
```

Get quick help:

```shell
docker run --rm -e "DEBUG=1" ghcr.io/nicc777/py-animus:latest -h
```

Use (as per the [hello world example](https://github.com/nicc777/py-animus/tree/main/doc)):

```shell
docker run --rm -e "DEBUG=1" \
  -v $PWD/examples/hello-world/src:/tmp/src \
  -v $PWD/examples/hello-world/manifest:/tmp/data \
  -v /tmp/results:/tmp/hello-world-result \
  ghcr.io/nicc777/py-animus:latest apply -m /tmp/data/hello-v1.yaml -s /tmp/src
```

The above command will create a file in `/tmp/results` with the content as defined in the manifest file:

```shell
$ cat /tmp/results/output.txt
This is the contents of the file
specified in the content property
of the spec.
```

More complex example:

```shell
docker run --rm -e "DEBUG=1" \
  -v $PWD/examples/linked-manifests/src:/tmp/src \
  -v $PWD/examples/linked-manifests/manifest/round_1:/tmp/data \
  -v /tmp/results:/tmp/example-page-result \
  ghcr.io/nicc777/py-animus:latest apply -m /tmp/data/linked-v1.yaml -s /tmp/src
```

To reverse out any of the applied commands, just use the command `delete` instead of `apply`

The file will no longer be available

```shell
$ cat /tmp/results/output.txt
cat: /tmp/results/output.txt: No such file or directory
```

# Acknowledgements

## Icons

* <a href="https://www.flaticon.com/free-icons/yaml" title="yaml icons">Yaml icons created by shohanur.rahman13 - Flaticon</a>
* Terraform icon obtained from [Terraform Press Kit](https://www.terraform.io/)
* Bash icon from the [Official GNU Bash Logo Repository](https://github.com/odb/official-bash-logo)
* Other icons from stencils in [draw-io](https://draw-io.net/)
* Python Logo from [the Python Software Foundation](https://www.python.org/community/logos/)