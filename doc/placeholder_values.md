
- [Placeholder Values](#placeholder-values)
- [Guidelines and Best Practices](#guidelines-and-best-practices)
  - [Syntax for the Placeholder](#syntax-for-the-placeholder)
  - [Environments](#environments)
  - [Variables and Manifest Dependencies](#variables-and-manifest-dependencies)


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

The general syntax is: `{{ .Values.<<name>> }}` or `{{ .Variables.<<name>> }}`

Note the following rules:

* Start with `{{`
* End with `}}`
* There must be exactly ONE space between `{{` and the either `.Values.` or `.Variables.`
* `.Values.` or `.Variables.` indicates the kind of value replacement, and in the case of `.Values.` it expects the value to come from a values file. The `.Variables.` type indicates the value to originate from a stored variable, typically as a result of a previous applied manifest which typically produces variable values. 
* After `.Values.` the `<<name>>` represents the variable name to be used as a lookup in the values file. It maps to the `name` field. General rules:
    * Start with an alpha character ([ASCII](https://en.wikipedia.org/wiki/ASCII) decimal values 65 to 80 (inclusive) and 97 to 122 (inclusive))
    * May include other printable ASCII characters like any of the following: `- _ = +` (and more)
    * Length is not strictly enforced, but keep it reasonable - it is after all for your own benefit.
    * Unicode may work - but your milage may vary. Stick to ASCII

## Environments

If an environment is not specified on the command line, the default environment named `default` will be used.

It is therefore good practice to always have a `default` environment value defined for every variable in the values file. 

Another consideration comes from the principle of "_fail securely_" and in this context the default value should point to a non-production or non-critical environment value, like the `sandbox` environment in the example.

Although not strictly required, define values for every environment used in all the manifests to ensure proper coverage and edge cases.

When no variable for an environment is found, the placeholder value will be used literally - this is the current behavior, but may change in the future.

## Variables and Manifest Dependencies

Assume you have the following Manifest Implementations:

```python
# File: my-custom-manifest-implementation-for-service-x.py
from py_animus.manifest_management import *
from py_animus import get_logger, parse_raw_yaml_data

class MyServiceX(ManifestBase):

    def __init__(self, logger=get_logger(), post_parsing_method: object = my_post_parsing_method, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def _var_name(self, target_environment: str='default'):
        return '{}:{}:{}'.format(
            self.__class__.__name__,
            self.metadata['name'],
            target_environment
        )

    def apply_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders()):
        variable_cache.store_variable(
            variable=Variable(
                name='{}:VAL_X'.format(self._var_name(target_environment=target_environment)), 
                initial_value='Hello'
            )
        )
        # remaining implementation logic omitted...
    
    # Other methods omitted...



# File: my-custom-manifest-implementation-for-service-y.py
from py_animus.manifest_management import *
from py_animus import get_logger, parse_raw_yaml_data

class MyServiceY(ManifestBase):

    def __init__(self, logger=get_logger(), post_parsing_method: object = my_post_parsing_method, version: str='v1', supported_versions: tuple=('v1',)):
        super().__init__(logger=logger, post_parsing_method=post_parsing_method, version=version, supported_versions=supported_versions)

    def _var_name(self, target_environment: str='default'):
        return '{}:{}:{}'.format(
            self.__class__.__name__,
            self.metadata['name'],
            target_environment
        )

    def apply_manifest(self, manifest_lookup_function: object=dummy_manifest_lookup_function, variable_cache: VariableCache=VariableCache(), increment_exec_counter: bool=False, target_environment: str='default', value_placeholders: ValuePlaceHolders=ValuePlaceHolders()):
        variable_cache.store_variable(
            variable=Variable(
                name='{}:VAL_Y'.format(self._var_name(target_environment=target_environment)), 
                initial_value='{}'.format(self.spec['greetingText'])
            )
        )
        # remaining implementation logic omitted...
    
    # Other methods omitted...
```

The variable from a manifest of service X can now be re-used in service Y with the following hypothetical manifests:

```yaml
---
kind: MyServiceX
version: v1
metadata:
  name: service-x
spec:
  greeting: 'Hello'
---
kind: MyServiceY
version: v1
metadata:
  name: service-y
  dependencies:
    apply: 
    - service-x
spec:
  greetingText: 'I say: {{ .Variables.MyServiceX:service-x:default:VAL_X }} world!'
#                           \___  __/ \____  __/ \___  __/ \__  _/ \_  _/
#                               \/         \/        \/       \/     \/
#                       Type of Lookup     |  Manifest Name   | Variable Name
#                                     Manifest Type      Environment
```

> **Note**
> In the unittest file `tests/test_manifest_management.py` in test class `TestManifestBaseVariableSubstitutionDemo` this exact scenario is tested.

The result is that in the variable named `MyServiceY:service-y:default:VAL_Y`, the final calculated value would be `I say: Hello world!`
