Quick Navigation: [Documentation home](../../README.md) | [Up](./README.md)

<hr />

- [How to use Values](#how-to-use-values)
- [Organizing Values Manifests](#organizing-values-manifests)
- [See Also](#see-also)


# How to use Values
     
In the [environments](./06-environments.md) section, a brief demonstration was already provided of how values can be used.

The values manifest differs slightly from other manifests in that the `metadata` section only takes a `name` field and any other supplied fields will have no effect. Full manifest documentation is available in the [extension documentation section](../03-standard-extensions-documentation/02-special/02-values.md).

Values is a powerful way to define field values that may have to be different for different environments.

A good example would be different domains that you have for different accounts. There might be a scenario where you want to do something in each account where you require the domain name for each account. You could accomplish this by something like the following:

```yaml
---
kind: Values
version: v1
metadata:
  name: per-account-dns-host-name
spec:
  values:
  - valueName: demo-value
    defaultValue: 'sandbox-domain'
    environmentOverrides:
    - environmentName: sandbox
      value: 'sandbox-domain'
    - environmentName: test
      value: 'test-domain'
    - environmentName: production
      value: 'primary-domain'
```

Values are referenced directly or by using the special YAML tag `!Sub`:

* When requiring ONLY the value with no other string values, reference the value directly with:

```yaml
---
kind: WriteFile
version: v1
metadata:
  name: write-selected-dns-host
  environments:
  - sandbox
  - test
  - production
spec:
  data: !Value demo-value
  targetFile: /tmp/reference-domain.txt
```

* In more complex strings where the value must be substituted within a string, the special YAML tag `!Sub` can be used:

```yaml
---
kind: WriteFile
version: v1
metadata:
  name: write-selected-dns-host
  environments:
  - sandbox
  - test
  - production
spec:
  data: !Sub 
  - 'The host ${host} was references'
  - host: !Value demo-value
  targetFile: /tmp/reference-domain.txt
```

# Organizing Values Manifests

There are several ways that you can organize values. You can bundle ALL values in a single file, or use separate files. Regardless, values are ingested by referencing them in a Project manifest. Look at teh following Project manifest [from this example](../../../examples/projects/simple-02/001-parent/demo-project-root.yaml):

```yaml
spec:
  valuesConfig:
  - https://raw.githubusercontent.com/nicc777/py-animus/main/examples/projects/simple-02/values/demo-project-values.yaml
```

As you can see, the `valuesConfig` field takes a list of strings, where each list item is either a PATH or an URL to a YAML file containing `Values` manifests. When these files are processed for values, _ALL_ other manifest types are ignored, and it is therefore possible to reference values defined in another YAML file containing also other manifests which will all be ignored unless specifically referenced in other fields in the project.

The same `Values` manifest can also be referenced multiple times, and the values will only be loaded once. If there are `Values` manifests with the same name in multiple files that are referenced, only the _FIRST_ referenced instance will be ingested.

# See Also

* [Values Manifest Documentation](../03-standard-extensions-documentation/02-special/02-values.md)
* [What is a resource](./01-what-is-a-resource.md)
* [What is a "_Desired State_"](./02-what-is-desired-state.md)
* [Defining desired resource state in a Manifest](./03-defining-desired-resource-state-in-a-manifest.md)
* [Actions that can be performed to enforce resource state](./04-actions-that-can-be-performed-to-enforce-resource-state.md)
* [Extensions for every resources](./05-extensions-for-every-resources.md)
* [How to think of Environments](./06-environments.md)
* [Using Variables](./08-variables.md)
* [Planning and Project Hierarchy, Dependencies and Other Consideration](./09-planning-and-hierarchy.md)

<hr />

Quick Navigation: [Documentation home](../../../README.md) | [Up](./README.md)