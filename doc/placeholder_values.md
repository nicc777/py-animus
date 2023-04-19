
- [Placeholder Values](#placeholder-values)
- [Guidelines and Best Practices](#guidelines-and-best-practices)
  - [Syntax for the Placeholder](#syntax-for-the-placeholder)


# Placeholder Values

Assuming you have a manifest with more than one [environment](target_environments.md) setup, it may be required to have some values for fields be different, depending on the environment.

A typical example may be to reference a AWS S3 bucket, where each environment refers to a different S3 bucket. A very hypothetical example manifest may look like this:

```yaml
---
kind: MyHypotheticalKind
version: v1
metadata:
    name: data-from-s3
    environments:
    - sandbox
    - test
    - prod
spec:
    s3BucketName: '{{ .Values.source-s3-bucket }}'
    s3Key: 'some-key'
```

A values file can now be defined as follow:

```yaml
# Example values file: /tmp/values.yaml
---
values:
- name: source-s3-bucket 
  environments:
  - environmentName: sandbox
    value: my-sandbox-s3-bucket-name
  - environmentName: test
    value: my-test-s3-bucket-name
  - environmentName: prod
    value: my-prod-s3-bucket-name
  - environmentName: default
    value: my-sandbox-s3-bucket-name
```

Using the command line parameter `-f` or `--file`, the values file(s) can be added to the apply or delete action. 

If, for example, the command line parameter `-e` (or `--env`) has a value of `test`, the `spec.s3BucketName` value will be changed to `my-sandbox-s3-bucket-name`.

# Guidelines and Best Practices

## Syntax for the Placeholder

The general syntax is: `{{ .Values.<<name>> }}`

Note the following rules:

* Start with `{{`
* End with `}}`
* There must be exactly ONE space between `{{` and `.Values.`
* `.Values.` indicates the kind of value replacement, and in this case it expects the value to come from a values file. In the future other types of sources will also be supported, for example a secrets store of some kind.
* After `.Values.` the `<<name>>` represents the variable name to be used as a lookup in the values file. It maps to the `name` field. General rules:
    * Start with an alpha character ([ASCII](https://en.wikipedia.org/wiki/ASCII) decimal values 65 to 80 (inclusive) and 97 to 122 (inclusive))
    * May include other printable ASCII characters like any of the following: `- _ = +` (and more)
    * Length is not strictly enforced, but keep it reasonable - it is after all for your own benefit.
    * Unicode may work - but your milage may vary. Stick to ASCII

TODO
