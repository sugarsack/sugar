# Hacking

## Requirements

To successfully setup your development environment, the following requirements should be met:

- Python 3.5+
- OpenSSL tools

If you are on Ubuntu/Debian, make sure the following packages are installed:
 - `python3.5-dev` (in case Python 3.5)
 - `python3-venv`

## Setting up dev environment

Since Sugar Project is on the very early stage, please help improving this process
if it fails on your operating system. There are two ways of setting up your
development environment:

- Bootstrapping (preferred)
- Manual (if bootstrapping doesn't work for you)

```Important:: Bootstrapping was currently tested only on Ubuntu LTS 16.04 and 18.04.
```

### Bootstrapping

To start contributing to Sugar, please follow the following steps:

1. Create an empty directory where GitHub repo and virtual environment is going
to be created and navigate there:

       mkdir sugarsack
       cd sugarsack

2. Being in that directory, now download shell script that will do the rest for
you (please just copy-paste the below):

       wget https://raw.githubusercontent.com/sugarsack/sugar/master/dev/setup-dev-env
       
   Or the same with `curl` if you do not have `wget` installed:
   
       curl https://raw.githubusercontent.com/sugarsack/sugar/master/dev/setup-dev-env -o setup-dev-env
       
   This script is in the same repository as you are going to download.
   You can [review its content](https://github.com/sugarsack/sugar/blob/master/dev/setup-dev-env) before executing on your machine.

3. Run it with Bash:

       bash setup-dev-env

   What it will do:
   
     - Check if you have installed Python 3.5 or greater version.
     - Check if you have installed OpenSSL tools.
     - Setup virtual environment in your current directory, called `sugar-env`.
     - Clone the GitHub repo into your current directory, called `sugar`.
     - Make a symbolic link in your home `~/.sugar` pointing to the `sugar/etc/sugar` directory.

   On the moment when bootstrapping will generate SSL certificate,
   please answer typical for OpenSSL certificate generator questions or simply
   press <ENTER> key on each question.

4. At the end of the bootstrapping process, you will see the last notification,
which will ask you to `source` into your shell (Bash) Python virtual environment
and modify your `$PATH` environment variable, which will add `sugar` command.
If you've just missed it (or forgot), simply `source` the `sugarsack/sugar/dev/hacking`
file.

   This is the step you will be always repeating while starting the terminal.

### Manual

OK, seems bootstrapping failed for you and thus you're here. Sorry for that...
To setup manually developing environment for Sugar, please go through the following steps:

1. Make sure you have `python` available as 3.5 version or better. As well make sure
`openssl` tool is avilable.

2. Clone Git repository of `sugar`:

       git clone git@github.com:sugarsack/sugar.git

3. Prepare tools for Python virtual environment. Depending on what OS you are, but for example,
if you are on Ubuntu/Debian, you should additionally install `python3-venv`:

       sudo apt-get install python3-venv

4. Create virtual environment for Python3 and call it `sugar-env`:

       python3 -m venv sugar-env

5. Activate it:

       source sugar-env/bin/activate

6. Upgrade your PIP and then install all the dependencies. To do so, please issue the following commands:

       pip install --upgrade pip
       pip install -r sugar/requirements.txt
       pip install service_identity --force --upgrade
       pip install git+https://github.com/rtfd/recommonmark.git

7. Right now it is still needed to link the entire library to your Python installation. For that,
navigate to your `sugar` repository and link inner `sugar/` directory to the Python's `site-packages`.
For example, assuming you are running Python 3.5 and your virtual environment is called `sugar-env`,
your command will look something like this:

       cd sugar
       ln -s $(pwd) ../../sugar-env/lib/python3.5/site-packages/sugar

8. From the `sugarsack` main directory, update your `hacking` environment which you will import
every time into your Bash environment:

       echo "PATH=\"$(pwd)/sugar/bin:\$PATH\"" >> "$(pwd)/sugar/dev/hacking"
       echo "source $(pwd)/sugar-env/bin/activate" >> "$(pwd)/sugar/dev/hacking"

9. Generate SSL certificates. Being in `sugarsack` directory, do the following:

       mkdir sugar/etc/sugar/ssl
       cd sugar/etc/sugar/ssl
       ../../../dev/gen_ssl.sh
       
   This will generate three files in the current `ssl` directory:
   
     - `certificate.p12`
     - `certificate.pem`
     - `key.pem`
   
   Rename `certificate.pem` and `key.pem` according to the configuration in `etc/sugar/master.conf` file.

10. Sugar is looking for its configuration in the following directories:
 
     - `/etc/sugar`
     - `~/.sugar`
   
11. As you probably don't want to have a system global `/etc/sugar` directory, you should create a symbolic link
   `~/.sugar` to the current configuration. From the main `sugarsack` directory, issue the following command:
   
        ln -s $(pwd)/sugar/etc/sugar $HOME/.sugar

11. Hopefully now we're all set up!

    One more thing: as you're at this step already, please update the process of bootstrapping script
so it won't fail for the environments like yours, and make a [Pull Request to
Sugar repository](https://github.com/sugarsack/sugar). Thanks alot, ahead!

## Running Sugar

Sugar has command line interface, similar to Git. That is, all Sugar sub-applications are
called under `sugar` command umbrella: `sugar master --help`, `sugar client --help` and so on.

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

    $ sugar master -l debug -L STDOUT

Next, from another activated environment you can start Sugar Client:

    sugar client -l debug -L STDOUT


And finally, from the third activated environment you should be able to manage keys
and issue Sugar commands. For example, now Master should have one pending key from
the newly running client:

    sugar keys list

For more help on `keys`, call `sugar keys --help`.

## Running Linter/Code Checks

TBD

## Running tests

TBD

## First Quick Tips

### Logging

#### Levels

Logging level is always taken from the configuration. If you want it in `debug` then
please setup so.

#### Output

At any time you can always override logging output. If Sugar is configured to log to
some file and you need it on a screen right away, add `-L STDOUT` at any time.

#### Look at tracebacks

You can always raise level to `debug` by adding `-l debug` parameter anywhere. But
this _in addition to changing logging level_ will include full Python tracebacks,
once something went wrong.

### Pull Requests

If you make a Pull Request, please make sure that:

- Lint checkers aren't failing (all of them). Refer to "Running Linter/Code Checks" section.
- No existing tests are broken
- Your tests are written. :-)
