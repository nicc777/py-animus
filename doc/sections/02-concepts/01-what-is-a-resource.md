Quick Navigation: [Documentation home](../../README.md) | [Up](./README.md)

<hr />

- [What is a Resource](#what-is-a-resource)
- [See Also](#see-also)

# What is a Resource
     
At it's most basic level, a resource is some infrastructure object that can be defined and managed through a concept known as [Infrastructure as Code](https://en.wikipedia.org/wiki/Infrastructure_as_code) (wikipedia). The phrase can also be abbreviated to `IaC`

By defining the [desired state](./02-what-is-desired-state.md) through [manifest files](./03-defining-desired-resource-state-in-a-manifest.md), the [extension(s)](./05-extensions-for-every-resources.md) responsible for that kind of resource will try to apply changes achieve the estate as expressed or defined in the manifest.

A resource could be any of the following:

* A virtual machine (VM).
* A virtual network interface
* Virtual storage, for example blob storage or network storage 
* Virtual networking components like load balancers and firewalls

The aim of `py-animus` is also to integrate with several existing IaC solutions including [AWS CloudFormation](https://en.wikipedia.org/wiki/AWS_CloudFormation) and [Terraform](https://en.wikipedia.org/wiki/Terraform_(software)). 

`py-animus` should be seen as complimentary to these services and not as an attempt to replace them. In fact, `py-animus` exist in order to orchestrate more complex IaC scenarios that may involve orchestrating deployment and management of infrastructure using a combination of such technologies spanning several different cloud providers.

Therefore, a good use case for `py-animus` is the orchestration of IaC between different cloud providers (like AWS and Microsoft Azure) that may have each defined infrastructure in different tool sets, including Terraform and AWS CloudFormation templates.

Of course moist of the functionality could be achieved by only using a tool like Terraform, and `py-animus` only really serves a purpose in scenarios where this is not possible,

In this context, the provisioning and management  of resources through IaC is managed by `py-animus` by delegating the implementation to extensions that support those specific third-party IaC implementations (Terraform, AWS CloudFormation etc.).

Without any extensions, `py-animus` has some limited capabilities implemented through [standard extensions](../03-standard-extensions-documentation/README.md) that can perform some basic orchestration. The most generic extension, for example, is the [ShellScript](../03-standard-extensions-documentation/03-other/02-shell-script.md) extension that allows users to run virtually any command and such an extension could be used to provision virtually any resource for which a command is available on the management system. This approach allows engineers to keep all IaC definitions in the same manifest repository and under management of the same tool until more specialized extensions become available or are developed in house.

# See Also

* [What is a "_Desired State_"](./02-what-is-desired-state.md)
* [Defining desired resource state in a Manifest](./03-defining-desired-resource-state-in-a-manifest.md)
* [Actions that can be performed to enforce resource state](./04-actions-that-can-be-performed-to-enforce-resource-state.md)
* [Extensions for every resources](./05-extensions-for-every-resources.md)
* [How to think of Environments](./06-environments.md)
* [How to use Values](./07-values.md)
* [Using Variables](./08-variables.md)
* [Planning and Project Hierarchy, Dependencies and Other Consideration](./09-planning-and-hierarchy.md)

<hr />

Quick Navigation: [Documentation home](../../../README.md) | [Up](./README.md)