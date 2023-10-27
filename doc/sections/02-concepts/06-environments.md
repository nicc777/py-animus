Quick Navigation: [Documentation home](../../README.md) | [Up](./README.md)

<hr />

- [How to think of Environments](#how-to-think-of-environments)
- [See Also](#see-also)

# How to think of Environments
     
An environment in `py-animus` is a way of thinking about how you can target the same manifests to different targets (think of it as a "_where_") for various purposes.

For example, you may have different cloud accounts allocated for "development", "testing" and "production". In a cloud provider like Microsoft Azure, you could even link environments to combinations of resource groups or subscriptions. 

However, end-users can easily come up with their own constructs and in combination with `Projects` it is possible to really organize your complete IaC landscape very granular - if you so whish.

Keep in mind that from an Infrastructure team's perspective, they would probably see the environments of the development teams all as "production" environments, because they have their clients (the development teams) using Infrastructure resources in the software development process. But the IaC engineers themselves also need sandbox or development environments as well as testing environments to ensure their IaC solutions work before committing it to what can be perceived as the production environment that all other clients use.

It is also possible to define a single manifest that has different spec values depending on an environment. This is accomplished through the use of [values manifests](./07-values.md) which defines specific values of each selected field for different environments.

In a typical manifest, the environment is defined in the `metadata` section. If no environment is defined, the manifest automatically belongs to the `default` environment. Consider the following example:

```yaml
---
kind: ShellScript
version: v1
metadata:
  name: shellscript-demo
  skipDeleteAll: true
  environments:
  - sandbox1
  - sandbox2
  - test
  - production
spec:
  source:
    type: inline
    value: !Sub
    - 'echo "Action: ${action} was run with value ${someValue}"'
    - action: !Variable std::action
      someValue: !Value demo-value
---
kind: Values
version: v1
metadata:
  name: demo-values
spec:
  values:
  - valueName: demo-value
    defaultValue: 'A'
    environmentOverrides:
    - environmentName: sandbox1
      value: 'B'
    - environmentName: sandbox2
      value: 'C'
    - environmentName: test
      value: 'D'
    - environmentName: production
      value: 'E'
```

When `py-animus` is run, the command line arguments include the targeted environment. for example `sandbox2`. The extension will then apply the values as defined in the spec and where references to `Values` were made, the appropriate value for the selected environment will be used. If a specific environment value is not defined, the `defaultValue` is used for that environment.

It is also possible to apply certain manifests in certain environments and not others. For example:

```yaml
---
kind: ShellScript
version: v1
metadata:
  name: shellscript-1
  skipDeleteAll: true
  environments:
  - sandbox1
spec:
  source:
    type: inline
    value: 'echo 1'
---
kind: ShellScript
version: v1
metadata:
  name: shellscript-2
  skipDeleteAll: true
  environments:
  - sandbox2
spec:
  source:
    type: inline
    value: 'echo 1'
---
kind: ShellScript
version: v1
metadata:
  name: shellscript-3
  skipDeleteAll: true
  environments:
  - sandbox1
  - sandbox2
spec:
  source:
    type: inline
    value: 'echo 2'
```

In the above example, `shellscript-1` will only be processed in environment `sandbox1`, and `shellscript-2` will only be processed in environment `sandbox2`, but `shellscript-3` will only be processed in both environments `sandbox1` and `sandbox2`.

The use of environments provide great flexibility for IaC engineers to keep all IaC organized in a single repository, but still have the ability and flexibility to define what IaC manifests can applied where.

# See Also

* [What is a resource](./01-what-is-a-resource.md)
* [What is a "_Desired State_"](./02-what-is-desired-state.md)
* [Defining desired resource state in a Manifest](./03-defining-desired-resource-state-in-a-manifest.md)
* [Actions that can be performed to enforce resource state](./04-actions-that-can-be-performed-to-enforce-resource-state.md)
* [Extensions for every resources](./05-extensions-for-every-resources.md)
* [How to use Values](./07-values.md)
* [Using Variables](./08-variables.md)
* [Planning and Project Hierarchy, Dependencies and Other Consideration](./09-planning-and-hierarchy.md)

<hr />

Quick Navigation: [Documentation home](../../../README.md) | [Up](./README.md)