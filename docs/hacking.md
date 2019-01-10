# Hacking

## Setting up dev environment

To start developing Sugar, to the following steps:

1. Check out Git repository:

```
   git clone git@github.com:sugarsack/sugar.git
```

2. Prepare tools for Python virtual environment. Depending on what OS you are, but for example,
if you are on Ubuntu/Debian, you should additionally install `python3-venv`:

```
   sudo apt-get install python3-venv
```

3. Create virtual environment for Python3 and call it for example "sugar-env:

```
   python3 -m venv sugar-env
```

4. Activate it:

```
   source sugar-env/bin/activate
```

5. Upgrade your PIP and then install dependencies. To do so, please issue the following commands:

```
   pip install --upgrade pip
   pip install -r sugar/requirements.txt
   pip install service_identity --force --upgrade
   pip install git+https://github.com/rtfd/recommonmark.git
```

6. Right now it is still needed to link the entire library to your Python installation. For that,
navigate to your `sugar` repository and link inner `sugar/` directory to the Python's `site-packages`. For example,
assuming you are running Python 3.7 and your virtual environment is called `sugar-env`, your command
will look something like this:

```
   cd sugar
   ln -s $(pwd) ../../sugar-env/lib/python3.7/site-packages/sugar
```

7. At last, export your local `bin/` to the common `PATH`. From the Git repo do the following:

```
   cd bin
   export PATH="$(pwd):$PATH"
```

8. Sugar also is looking for its configuration either in `/etc/sugar` or `~/.sugar` directories.
For your convenience, you can create `etc/sugar` subdirectory in the Git repo and symlink it there:

```
cd
ln -s .sugar /path/to/your/gitrepo/with/sugar/etc/sugar/

```

## Running Sugar

After environment is setup, at this point you should be able to run Sugar:

```
$ sugar
usage: sugar [<target>] [<component>] [<args>]

Target is a name or a pattern in Unix shell-style
wildcard that matches client names.

Available components:

    master     Used to control Sugar Clients
    client     Receives commands from a remote Sugar Master
    keys       Used to manage Sugar authentication keys
    local      Local orchestration

```

To start Sugar Master and see events right in the console, run the following:

```
$ sugar master -l debug -L STDOUT

```

Next, from another activated environment you can start Sugar Client:

```
sugar client -l debug -L STDOUT

```



## Running Linter/Code checks

TBD

## Running tests

TBD
