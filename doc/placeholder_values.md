
- [Placeholder Values](#placeholder-values)
- [Guidelines and Best Practices](#guidelines-and-best-practices)


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

TODO
