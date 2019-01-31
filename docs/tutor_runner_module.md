# Building a Simple Module

``` important:: This tutorial is subject to change or be (a bit) different from the actual implementation before the first Sugar release.
```

## Overview

Let's build a very basic module to get a platform name.
Our module is going to output the information about the platform.

Sugar supports only modules, written in Python language.

In a nutshell, here is are generally steps to do:

1. Setup a development environment.
2. Create a dummy module with `sugar-mkmod` command.
3. Modify the result and run it!
4. Documenting your module

## Setup a Dev Environment

This document won't cover it, since it is already described
in the [documentation how to do this](http://www.sugarsack.org/docs/hacking.html#setting-up-dev-environment).

As you already at development stage, it is assumed you've already
done this.

## Create a Scaffold Module

Sugar SDK, which is installed together with the development
environment brings a bunch of additional commands for you. One
of the useful commands you would like to run now is `sugar-mkmod`.

Depending on type you choose (runner or state), it will create
a dummy (but functional!) module for you. Let's just do it:

```
$ sugar-mkmod 
usage: sugar-mkmod [-h] [-n NAME] [-t {runner,state}] [-i IMPL]

optional arguments:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  Name of the module with the namespace. Example:
                        'foo.bar.mymodule'.
  -t {runner,state}, --type {runner,state}
                        Type of the module.
  -i IMPL, --impl IMPL  Imlementation name. Default: linux

General error: Type expected either to be 'runner' or 'state'.
```

Well, OK. It asks you to select module for being "runner" or "state".
We will leave out the "implementation" option as the default. 
In this Tutorial we are creating **runner module**.

```
$ sugar-mkmod -n system.name -t runner
```

The command above means that we've just created a module `name` in the
namespace `system`. So it will be accessible something like this:

```
$ sugar <host_name> system.name.<func_name>

```

After running the above, you should see something similar to this:
```
Runner module has been generated to
/home/sugar/lib/python3.7/site-packages/sugar/modules/runners/system/name
```
The path above will be different in your case. The end of it is more important:

```text
.../runners/system/name
```

Well, you've just created a fully functional module for Sugar, which is not
just yet ready for what we want to achieve.

## Modify Your Scaffold Module

Let's turn our module into the real deal. First let's see what we've got and
how its structure looks like.

### Explore what we've got

Navigate to the path you've just seen above and explore what we have got here:

```text
-rw-rw-r-- 1 sugar cfgmgmt 611 Jan 29 19:35 doc.yaml
-rw-rw-r-- 1 sugar cfgmgmt 246 Jan 29 19:35 examples.yaml
drwxrwxr-x 2 sugar cfgmgmt  39 Jan 29 19:35 _impl
-rw-rw-r-- 1 sugar cfgmgmt  15 Jan 29 19:35 __init__.py
-rw-rw-r-- 1 sugar cfgmgmt 467 Jan 29 19:35 interface.py
```

The implementation directory `_impl` contains the following:

```text
-rw-rw-r-- 1 sugar cfgmgmt  15 Jan 29 19:35 __init__.py
-rw-rw-r-- 1 sugar cfgmgmt 889 Jan 29 19:35 linux.py
```

### Define the interface

We will be now defining an interface for the platform report.

Open the `interface.py` in your favorite [`$EDITOR`](https://www.gnu.org/software/emacs/) 
and change its content to this:


```python
class NameInterface(abc.ABC, BaseRunnerModule):
    """
    Interface of the module 'name'.
    """

    @abc.abstractmethod
    def platform(self) -> dict:
        """
        Report system name

        :returns: string with the platform name
        """
```

Well, that's it.


```important:: The docstrings are **not the documentation** yet! However, please always write them correctly.
```

Let me explain you a bit what is going on above. Python does not have the interfaces
per se like in Java. Because Java does not supports a multiple inheritance at first place.
In Python interface is just that: an abstract class. As long as there are methods with the
annotation `@abc.abstractmethod`, they _have_ to be overloaded in the subsequent subclass
we will be implementing soon. Each of your implementation has to subclass from this
interface (or it will not be recognised and won't be loaded).

If you forgot to implement at least one of the abstract methods in this interface, your
module _implementation_ will not load (others theoretically might go in, if they implement
everything correctly).

We also annotated the interface that it returns a dictionary, which is _always_ in case
for Sugar.

### Defining Output Schema

Now, while this is not _necessary_ to define all the output structure ahead, it is recommended
so. Here is how do we define it:

```yaml
NameInterface:
  platform:
    r:name: str
    cpu: str
```

In this case we are telling that our module will _always_ return the following data structure
(example):

```json
{"name":  "Linux"}
```

The little prefix `r:` in front of the `name` that makes it `r:name` means just that: **required**.
So every field with the prefix `r:` makes it required.

``` important:: Every time you use **"r:"** prefix for some field, it will make it **required**.
```

Additionally to that, _sometimes_ sometimes might return `cpu` value as well. This means that the
implementation is not _obligated_ to return the following:

```json
{"name": "Linux", "cpu": "x86_64"}
```


``` important:: You can always define output schema later, no stress!
```

### Implementation!

The implementation is the following:

1. Override the interface we've just defined
2. Obtain return object. More on this later.
3. Format the data of that object according to the schema.

To do this, modify the data accordingly:

```python
import platform
from sugar.modules.runners.system.name.interface import NameInterface


class NameModule(NameInterface):
    """
    Module to return platform name
    """

    def platform(self) -> dict:
        """
        Return the name of the platform.
        :returns: string with the platform name.
        """

        # Gather data we need
        name = platform.system()
        cpu = platform.processor()

        # Format result
        result = self.new_result()
        result.update({"name": name, "cpu": cpu})

        # Return it
        return result
```

Congratulations! Here, you have it. Was it hard?

Let's just walk-through what is happening in the above class:

1. You define a class `NameModule` and subclass it from
   the interface `NameInterface`.
2. Override method `platform` from the interface, so it is no longer an `@abc.abstractmethod`.
3. First, we call internal Python module `platform` and getting all the needed information for us.
4. Your module already has built-in method, called `new_result` which creates an instance of
   result class. 

### What is the Result Object?

Your module is calling `new_result` method to create an instance of a module result 
container. Essentially, result container object is just a regular Python dictionary but on 
steroids. It has additionally properties for carry an additional metadata, gathered during 
the function execution behind the scenes.

When your method is executed, Sugar connects to the logger channel and duplicates all the logging
data. When you return your result, this data is attached to it without modification of the
content of your result. Similar, if your function just crashed, Sugar will collect all the
data about it and return back to the master.

The master will use this information for further reporting and results storing.


### Making It a Bit More Specific

What if we want to add another implementation, say for SunOS? While in _this_ particular case
it is not really needed, but for the exercise sake we will add another implementation then.

In a nutshell, we should be able to add another implementation of the module for SunOS.
To do that, we create a file in the `_impl` directory with pretty much the same content as
for Linux platform. And then we override `__validate__` method, which would be called every
time your module is imported and raise an exception there. Since the `__validate__` method
is _also_ available in the interface class, we will use this to call it for all our platform-specific
version of our module. We could reuse this so we will write _less_ code to do _more_ here.

OK, let's just do this. 

Copy the `linux.py` to `solaris.py` and in both files add in the `NameModule` class a
static attribute `__platform__`, setting it to which platform this class should run on.


In your `solaris.py` file `NameModule` should be modified to this (comments and everything else
is just ommitted here for clarity):

```python
class NameModule(NameInterface):
    __platform__ = "Solaris"
    ...
```

And in your `linux.py` file you should define `__platform__` attribute to the following:
```python
class NameModule(NameInterface):
    __platform__ = "Linux"
    ...
```

Now, every time when Sugar will load in a sequence both of these implementations, it will first
time initialise it with `Solaris` and the next time with `Linux` on the same platform.
At this moment we should just compare on what platform we are running and raise an Exception
to let the initialisation bail out. While possible to do this in both implementations twice,
we will doing this in the same place, right in the interface class. Open it in your `$EDITOR`
and add the following method:

```python
import platform
class NameInterface(abc.ABC, BaseRunnerModule):

    __platform__ = None  # This will be overridden by the subclass

    def __validate__(self):
        assert self.__platform__ == platform.system()
```

This is it!

What will happen now? Sugar will load each module implementation one after another. Every time
it will trigger `__validate__` method. The `__platform__` attribute will be set either to `Linux`
or `Solaris` in other implementation. And then assertion will happen if the current implementation
is not for the current platform.

Easy, isn't it?

## Documenting Your Module

Please document your module. Please document your module. Please document your
module. Did I mentioned to document your module?.. :-)

As we already know from the module overview, documentation consists of the functions descriptions
and examples.

### Update User Documentation

Open `doc.yaml` in your `$EDITOR` and update the documentation accordingly and update
its content to something like this:

```yaml
module:
  name: system.name
  author: John Smith <john@thematrix.org>
  summary: Get the name of the platform
  synopsis: >
    This module is designed to return a name of the platform
    on which it is running. Supported platforms are: "Linux" and "Solaris".
  since_version: 1.0.0

tasks:
  platform:
    description:
      - Returns platform name and architecture.
```

Anything that is not in the module is not needed to be mentioned. Since the `platform`
function does not accepts any parameters, they should not be mentioned in the documentation.

### Update Examples

Time to explain our users how to use this module. Open `examples.yaml` in your `$EDITOR`
and add the usage examples:

```yaml

platform:
  commandline: >-
    sugar \* system.name.platform
```

We deliberately removed `description` as it is an optional field that describes
the function use. We also do not use `states` as this modules does not have state
module equivalent that would reuse it.

## Verify Integrity

Sugar SDK from version 0.0.7 contains `sugar-valmod` utility. It is invoked
by the following command:

```text
$ sugar-valmod --help
usage: sugar-valmod [-h] [-t {runner,state}] [-n NAME] [-a]

Sugar Module Validator, 0.0.1 Alpha

optional arguments:
  -h, --help            show this help message and exit
  -t {runner,state}, --type {runner,state}
                        Type of the module.
  -n NAME, --name NAME  Name of the module with the namespace. Example:
                        'foo.bar.mymodule'.
  -a, --all             Validate all modules (runners and state).
```

To verify our new runner module, issue this:

```text
$ sugar-valmod -n system.name -t runner
```

There should be the following output (might be different if the SDK version is other):

```text
 validation  >>>

Validating 'system.name' module
=======================================================================================================================================
  ...get meta (scheme, doc, example)
  ...get interface
  ...get implementations (1)
Verifying scheme
  (unsupported yet)
Verifying documentation
Verifying examples
Done verification.

  All seems to be OK!

```

In case documentation does not reflect how the interface looks like, or examples
aren't finished etc, this will give you a list of errors and warnings that you
should fix accordingly.

## Summary

Let's look back and see what we've already achieved with these very simple steps:

1. We have a module, which guarantees the same behaviour on different platforms.
2. Our module guarantees same data output on different platforms.
3. We can extend it now on Linux and Solaris and the implementations _aren't mixed into spaghetti_.
4. Module is properly documented and is visible through the CLI documentation subsystem
5. Users can see examples how to use it.

OK! You've just wrote your first Sugar module. In order to distribute it, you should
place it on your client machine to other modules. Best, if you create a pull request to
Sugar's GitHub repository and so the rest of the World will admire your work!
