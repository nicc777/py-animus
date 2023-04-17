# Target Environments

An environment is a fairly abstract concept and may mean different things to different people.

In the context of this project and environment is just a logical grouping that ties more than one manifest together during an action while other manifests not linked to the group is ignored. there are some exceptions that will also be discussed.

> **Note**
> An environment describes the servers, cloud accounts and other infrastructure components that must be targeted during an action. Many organizations will have some conceptual form of a `sandbox` and an `production` environment (at minimum). The `sandbox` environment is where developers and engineers experiment and test their projects before it is later deployed to the `production` environment. Other popular environments may include concepts like `test` environment and/or a `performance-test` environment. In very large organizations there may even be multiple of each of these. It is therefore good to think about a naming conventions for these environments.

This feature is also required for [the concept of placeholder values in manifests](placeholder_values.md), but does not rely on placeholders to be used at all.

Consider the following basic example hypothetical manifests:

```yaml
---
kind: MySuperCoolFeature
version: v1
metadata:
    name: feature1
    environments:
    - env1
    - env2
    - env3
spec:
    val: 1
---
kind: MySuperCoolFeature
version: v1
metadata:
    name: feature2
    environments:
    - env1
spec:
    val: 1
```

The manifest names `feature1` will be scoped for three environments (`env1`, `env2`, and `env3`) while `feature2` is only targeted  for one environment (`env1`).

If no environment is specified, the default named environment `default` will be used. If the value placeholder feature is used without specifying any environments in the manifest, always use the `default` name in the values files.

## Exceptions

<!-- Using the "manifest_lookup_function" instance for example -->

TODO
