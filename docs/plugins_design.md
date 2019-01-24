# Writing Modules

## Introduction

While Sugar Configuration Management System is heavily inspired by
Salt Open, modules in Sugar are very different than in Salt.

You might be thinking that adding a **simple function** into a module and
instantly return JSON just like Ansible does is _simple_. For a
primitive "Hello, World!" output probably yes, it is. And if your
module is all about to print "Hello, World!" then initial Sugar module
is quite more complex than that. However, if you are about to write a
_serious_ module that needs to pass data across the functions or do
various other complex things, you will quickly find out that your
"simple function" is already five screens scrolling, looks like a
spaghetti and you hate supporting that.

What you will do, if your module needs to separate implementations
across platforms? How to organise the dat flow so the grouped module
output of some virtual module returns at least the same data format by
default? How to split support between various owners so they will keep
an eye on their particular implementations? Because if this is all
together, you will end up with endless `if/else` chains.

This is where Sugar is designed for: to be able develop clean, complex
modules with better documentation.

## Module Types

Same as in Salt, there are two types of the modules:

- **Command module**. These are used to actually perform a task.
- **State module**. These are basically a proxy-modules that controlling
  command modules.

However, unlike in Salt, which has also two kinds of command modules, such
as "plain" and virtual, which can shares the same name but has
different implementations under the hood, Sugar keeps it simpler: all
modules are always equivalent to Salt's "virtual". This way each
module of Sugar always has an interface and at least one
implementation for specific platform.

While this sounds complicated and the word "interface" might render a
smirk on your face, in practice it is very simple. Moreover, you
probably want to keep end-user documentation separate from your
technical annotations of the code.

``` important:: All modules has a common interface, so the implementations behaves the same.
```

## Data Flow

Each module has a clear data definition for API and output. API are
made with a separate endpoint to the module function and are
versioned.

## Module Structure

While in other CfgMgmt systems module is usually just one file, Sugar
makes it more complex. To understand how module looks like, take a
look at the following diagram:

```
[optional namespace]
   <module name>
      <doc file>
      <examples file>
      <interface file>
      <implementations>
         <platform one>
         [platform two]
         [platform three]
	     ...
```

### Namespace

As you can see, the namespace is not always needed. But it is fully
supported. It helps organise your modules into a groups. For example,
all language-specific package managers you probably would like to keep
away from OS-specific package managers. So you will likely group
thins `lang.pip`,`os.pkg`, `system.net.`, `cloud.` etc. rather keep
all that in just one pile. Moreover, you probably want versioning,
something like `vm.something.v1`, `vm.something.v2` etc.

If you do not need all that, you just just omit the namespace!

``` important:: Namespace is not mandatory!
```

### Documentation

Documentation has different purposes in Sugar. You have documentation
for end-users with the examples etc, but you can have technical
short-written small summaries under each public function to keep you
focused working on it.

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

Example:

```
modules/runners/pkg/__init__.py
modules/runners/pkg/doc.yaml
modules/runners/pkg/interface.py
modules/runners/pkg/_impl/__init__.py
modules/runners/pkg/_impl/apt.py
modules/runners/pkg/_impl/zypper.py
modules/runners/pkg/_impl/dnf.py
```

The `interface.py` contains an interface of the `pkg` module.
The `__init__.py` is getting a loader of the module.

```
def get_module():
    return ModuleImplementation()

getattr(get_module(), func_name, *args, **kwargs)
```

Call:

```
system.os.pkg.install ...
syatem.lang.pip.install ...
```
