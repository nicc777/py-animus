# py_animus Documentation

> **note**
> At the moment the project is undergoing a major rewrite and the documentation is lagging behind a little. Much more updates coming shortly.

Documentation Structure:

* Quick start section
  * [Installing](./sections/01-quick-start/01-installing.md) `py-animus`
  * [First project and capability demonstration](./sections/01-quick-start/02-first-project-and-capability-demonstration.md)
* Concepts:
  * [What is a resource](./sections/02-concepts/01-what-is-a-resource.md)
  * [What is a "_Desired State_"](./sections/02-concepts/02-what-is-desired-state.md)
  * [Defining desired resource state in a Manifest](./sections/02-concepts/03-defining-desired-resource-state-in-a-manifest.md)
  * [Actions that can be performed to enforce resource state](./sections/02-concepts/04-actions-that-can-be-performed-to-enforce-resource-state.md)
  * [Extensions for every resources](./sections/02-concepts/05-extensions-for-every-resources.md)
* Standard Extension Documentation:
  * Logging Extension:
    * [Stream Logger](./sections/03-standard-extensions-documentation/01-loggers/01-stream-logger.md)
    * [Syslog logger](./sections/03-standard-extensions-documentation/01-loggers/02-syslog-logger.md)
    * [Datagram logger](./sections/03-standard-extensions-documentation/01-loggers/03-datagram-logger.md)
    * [File logger](./sections/03-standard-extensions-documentation/01-loggers/04-file-logger.md)
    * [Rotating File logger](./sections/03-standard-extensions-documentation/01-loggers/05-rotating-file-logger.md)
  * Special Extensions
    * [Project](./sections/03-standard-extensions-documentation/02-special/01-project.md)
    * [Values](./sections/03-standard-extensions-documentation/02-special/02-values.md)
  * Other Extensions:
    * [CLI Input](./sections/03-standard-extensions-documentation/03-other/01-cli-input.md)
    * [Shell Script](./sections/03-standard-extensions-documentation/03-other/02-shell-script.md)
    * [Git Repository](./sections/03-standard-extensions-documentation/03-other/03-git-repo.md)
    * [Web Resource Download](./sections/03-standard-extensions-documentation/03-other/04-web-download.md)
    * [Write File](./sections/03-standard-extensions-documentation/03-other/05-write-file.md)
* Third Party Extensions
  * [Introduction to extension and key concepts](./sections/04-third-party-extensions/01-intro.md)
  * [Extension Development Process](./sections/04-third-party-extensions/02-extension-development-process.md)
  * [Third party extension registry](./sections/04-third-party-extensions/03-registry.md)
