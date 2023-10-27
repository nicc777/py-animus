Quick Navigation: [Documentation home](../../README.md) | [Up](./README.md)

<hr />

- [Extensions for every resources](#extensions-for-every-resources)
- [See Also](#see-also)

# Extensions for every resources

The `py-animus` project relies on manifests that defines how resources will be created. More specifically, it orchestrates the deployment (or delete/cleanup) with some basic flow control and a way to dictate the order of operations. This whole process is defined in YAML manifest files, where each manifest file is implemented by a dedicated extension. An extension is therefore just the practical implementation of a what was expressed in the manifest linked to that extension.

The intention of extensions is to have one extension for a type of resource to manage. Through extensions there can also be support for other IaC tools. In fact, this is really the reason this project exists in the first place. 

The problem `py-animus` solves is to orchestrate different IaC tools targeting potentially different cloud environments without disrupting existing teams by dictating the use of different tools. 

It is important to remember that some organizations may already have an extensive library of IaC manifests used by different tools that was developed over several years. To port or re-implement this in another tool may not make financial or practical sense.

> **note**
> A good example of this problem is where a company may have two cloud providers managed by several different infrastructure/cloud teams. For example, they may target Amazon AWS and Microsoft Azure. In AWS they may have settled on CloudFormation as the IaC tool of choice and in Azure they may have settled on Terraform. In addition you may have Virtual Machine administrators using [Ansible](https://www.ansible.com/) to do finer grained VM configuration after deployment in both cloud environments. In these scenarios `py-animus` can be used as a kind of wrapper to bring these diverse worlds together and orchestrate how resources are provisioned across cloud providers using the existing tools and by by defining a hierarchy of dependencies there can also be finer grained control in the order of execution. 

The `py-animus` project will aim to provide some additional third party extensions, for example for AWS CloudFormation and Terraform, but for other tools, it may be possible to also just use wrappers like the `ShellScript` extension or you could also create your own extension and share it online.

# See Also

* [What is a resource](./01-what-is-a-resource.md)
* [What is a "_Desired State_"](./02-what-is-desired-state.md)
* [Defining desired resource state in a Manifest](./03-defining-desired-resource-state-in-a-manifest.md)
* [Actions that can be performed to enforce resource state](./04-actions-that-can-be-performed-to-enforce-resource-state.md)
* [How to think of Environments](./06-environments.md)
* [How to use Values](./07-values.md)
* [Using Variables](./08-variables.md)
* [Planning and Project Hierarchy, Dependencies and Other Consideration](./09-planning-and-hierarchy.md)

<hr />

Quick Navigation: [Documentation home](../../../README.md) | [Up](./README.md)