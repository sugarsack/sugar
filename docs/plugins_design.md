# Writing Modules

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



#################################################


## Data Flow

Each module has a clear data definition for API and output. API are
made with a separate endpoint to the module function and are
versioned.

## Module Structure

While in other CfgMgmt systems module is usually just one file, Sugar
makes it more complex. To understand how module looks like, take a
look at the following diagram:

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

The namespace and additional implementations are optional. The other
parts are mandatory.

### Namespace

As you can see, the namespace is not always needed. But it is fully
supported. It helps organise your modules into a groups. For example,
all language-specific package managers you probably would like to keep
away from OS-specific package managers. So you will likely group
thins `lang.pip`,`os.pkg`, `system.net.`, `cloud.` etc. rather keep
all that in just one pile. Moreover, you probably want versioning,
something like `vm.something.v1`, `vm.something.v2` etc.

If you do not need all that, you just just omit the namespace!

``` important:: Namespace is not mandatory! But it is good to have it and likely good to use it.
```

### Documentation

Documentation is defined in different places and thus have different
purposes in Sugar. You have documentation for end-users with the examples
etc, but you can have technical short-written small summaries under each
public function to keep you focused working on it.

#### Module Functions

This contains documentation how to use the particular module and its
functions.

#### Example Usage

This contains concrete samples of basic usage.

### Interface

### Implementations

A classic example. You want to install a package. But on what
operating system you are with what package manager of what version? Of
course, if you _already know_ your system or you do not mind to poke
it for "who are you?" (and generate more traffic).

However, Sugar is designed to help you out here. If you know a list of 
aliases of the same package, say on distribution X it is called `httpd`
and on distributoin Z it is called `nginx`, then you just pass a list of
aliases to the _same_ module, say called `pkg` and ask install _any of these_.
You don't know if this is Debian Linux or Arch Linux or even Solaris OS.
As long as you've got a list of the available names on all of these
platforms, Sugar will set it up for you transparently and you will get
the same result as on any other OS.

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

The `interface.py` contains an interface of the `pkg` module.
The `__init__.py` is getting a loader of the module.

