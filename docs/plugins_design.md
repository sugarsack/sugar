# Modules in Sugar (Overview)

## Introduction

Every decent configuration management software has modules. Many known
systems like Ansible, Puppet, Chef etc has modules and allow you to create
one.

### On simplicity

One might be thinking adding a **simple function** into a module and
instantly return JSON just like Ansible does is _simple_. Well, that
depends. It is for cure _quick_ and _easy_ to start with. But is it
really simple?

Simplicity is something that keeps being simple when your code grows.
In a nutshell, you will need to get back to your code in a year and still
understand how does it work!

What you will do, if your module needs to separate implementations
across platforms? How to organise the data flow in a way so the different
implementations still sticking to the same data structure? How would you
split support between various owners so they will keep an eye on their
particular implementations? How would you roll a generic (!) system that
would be able to pass arbitrary data from one function to another and
both are still "understand" each other?

This is where Sugar is designed for: to be able develop clean, complex
modules with the better documentation.

## Module Types

Same as in Salt, there are two types of the modules:

- **Runner module**. These are used to actually perform a task.
- **State module**. These are basically a proxy-modules that controlling
  command modules.
  
Additional to these two, user-defined custom modules. These are just a simple
Python modules with the arbitrary functions inside, pretty much something
like Ansible or Salt does.

### Runner modules

These modules _always_ should have the following:

1. Documentation file (YAML)
2. Examples file (YAML)
3. A common interface
4. At least one implementation of the interface
5. Schema of the interface, defining return structure (YAML)

While this sounds complicated and the word "interface" might render a
smirk on your face, in practice it is very simple. Moreover, you
probably want to keep end-user documentation separate from your
technical annotations of the code.

``` important:: Runner modules has a common interface and schema of returned data, so the implementations should behave exatly the same.
```

### State modules

These modules are designed to run one or more runner modules together
and organise them into the orchestration manner. They _always_ should
have the following:

1. Documentation file (YAML)
2. Examples file (YAML)
3. An implementation

These modules do not have any interface and a schema, because they
are always returning the same structure back:

1. Diff of changes, if any
2. Status: error, warning or success
3. General message

Additionally to that, each structure has a metadata of the logging
messages during the call of infos, warnings and errors.

## Module Structure

Modules in Sugar are a bit more complex than in alternative projects.
There are several reasons for this. To understand how each module looks
like, take a look at the following diagram of the **runner** module:

```
[namespace]
   <module name>
      <doc file>
      <examples file>
      <scheme file>
      <interface file>
      <implementations>
         <platform one>
         [platform two]
         [platform three]
         ...
```

**State** modules are a bit less complex, but still contains common
parts:

```
[namespace]
   <module name>
      <doc file>
      <examples file>
      <implementation>
```

Finally, custom modules that user can write on his own and they do not
have to be in Sugar main module tree is pretty straightforward:

```
[namespace]
   <module name & implementation>
```

Essentially, custom modules are just that: Python modules with just
arbitrary functions inside.

A typical runner module would have the following structure:

Example:

```
modules/runners/pkg/__init__.py
modules/runners/pkg/doc.yaml
modules/runners/pkg/examples.yaml
modules/runners/pkg/scheme.yaml
modules/runners/pkg/interface.py
modules/runners/pkg/_impl/__init__.py
modules/runners/pkg/_impl/apt.py
modules/runners/pkg/_impl/zypper.py
modules/runners/pkg/_impl/dnf.py
```

### Namespace

As you can see from the above examples, the namespace is not always
needed. But it is fully supported in Sugar. It helps organise your modules
into a groups. For example, all language-specific package managers
you probably would like to keep away from OS-specific package managers.
So you will likely group them like `lang.pip`,`os.pkg`, `system.net.` etc
rather than keep all that in just one pile. Moreover, you probably
want versioning, something like `vm.docker.v1`, `vm.docker.v2` where
are different APIs used.

If you do not need all that, you just can simply omit the namespace.

``` important:: Namespace is not mandatory! But it is good to have it and likely good to use it.
```

### Module Name

Module name is a directory after the namespace, if it exists. For example,
if you want to add module `system.net`, then the namespace `system` and the
module name would be `net`.

### Documentation YAML

Documentation is defined in different places and thus have different
purposes in Sugar. Unlike in other Python-based projects, Sugar does _not_
generate documentation from the source. Instead, documentation is described
in a YAML file that should be called always the same way: `doc.yaml`.

It has the following structure:

```yaml
module:
  name: system.test
  author: Your Name <your@cool.name>
  summary: Testing utilities
  synopsis: >
    System testing utilities for client health/heartbit: ping etc.
  since_version: 0.0.0

tasks:
  ping:
    description:
      - This function returns a text "pong" or anything else if specified.
      - Used to verify if client responds back to the master calls.
    parameters:
      text:
        description:
          - Specify alternative text to be returned by the `ping` function.
        required: false
        default: "pong"
        type: str

  some_func:
    description:
      - Some text
    parameters:
      ...
```

Documenting a module is basically documenting the interface for a runner module
or an implementatoin of a state module. This documentation is always for
end-users. 

### Example Usage YAML

Examples are described also in another, separate file, called `examples.yaml`.
It has the following structure:

```yaml
system.test:
  ping:
    description:
      - Data about this example.
      - Each item in this list is a sentence in the documentation.

    commandline: >-
      sugar \* system.test.ping
      sugar \* system.test.ping text='Hello, world!'
```

### Interface

Interfaces are present only for **runner** modules. Since each runner
module can contain more than one implementation for different back-ends
or operating systems, there should be a way to keep all of them consistent.

The interface file is typically called `interface.py` and contains only
**one** interface class, which describes all the functions of the module.
Any function that is not described in the interface will not be possible
to access.

The following rules should be kept, when adding another implementation:

- An implementation class should fail, raising an exception if the
  implementation does not fit to the current configurations.
  
- Every implementation class should keep function signatures exactly
  as the interface defines.

- Only defined methods in the interface will make them public to the
  specific implementation class.

### Return Data Scheme YAML

Similar to the interface, which is "input data" there should be also
consistency on "output data". Hence the scheme file defines scheme to
the type structure that is going to be returned from each function.

This is the same important as the interface, which makes runner module
consistent at the output. The scheme file is called `scheme.yaml` and
has the following structure:

```yaml
SystemInterface:
  os_name:
    r:cpu: str
    arch: str
```

The example above defines a function `os_name` in the interface
`SystemInterface`. This function returns two keys in the structure:

1. `cpu` which is of type "string" and is guaranteed to be always there.
2. `arch` which is also of type "string", but might not be there.

Optional data often depends on the underlying backend. For example,
packages in Windows are different than in Linux/RPM and their metadata
differ and at some places is the same. So the same data is usually
required and is the "lowest common denominator". The rest might be
there, but might be not.

### Implementations

Implementations are always stored in a sub-directory, called `_impl`.
They correspond to a specific underlying backend. For example, different
operating systems or different other backends etc. It is up to the
implementation to decide which one will bail-out and which will be kept.

Implementations are chosen in a pretty straight-forward way: instantiated
one after another. The rule here is very simple: one should stay, other
should bail-out. Typically it is done at the constructor `__init__` which
verifies if all dependencies are met, if the OS is supported, if all
backends are around etc.

If more than one implementation stays, conflicting situation appears and
such module cannot be loaded, but is going to be disabled. Such conflicting
situation is registered as an error and this needs to be fixed.

Why do we have different implementations, you can see in a classic example
installing a package. When you do that, it rather seems easy: just install
it. But on what operating system you are with what package manager of what
version? Of course, if you _already know_ your system or you do not mind
to poke it another time asking "who are you?", that likely not a problem
for you.

However, Sugar is designed to help you out here. In this classic example,
Sugar will select correct package manager and will pass correct package
name for the current distribution.

How does Sugar knows which package _name_ is to use on what distribution?
While there is a tooling to generate these sort of maps, they aren't always
reliable. And package in one OS might be called slightly different than in
the other. They also provide different dependencies etc. However, if you
know a list of  aliases of the same package that would pass through all
the variety of your possible operating systems, Sugar will eventually pass
through that one which is needed.

Say on a distribution X a package is called `httpd`. And on a distributoin Z
it is called `nginx`. In this case you just pass a list of aliases to the
_same_ module, say called `pkg` and ask install _any of these_.
You don't know if this is Debian Linux or Arch Linux or even Solaris OS.
As long as you've got a list of the available names on all of these
platforms, Sugar will set it up for you transparently and you will get
the same result as on any other OS.
