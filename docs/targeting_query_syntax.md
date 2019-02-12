# Targeting Clients

Targeting clients is specifying which client machine should run a
command or execute a state by matching against hostnames, or any other
system information, defined groups or combining all that.

For example the following command will restart Nginx server, running
on the machine `site.foo.com` and the command will run only exactly on
that machine:

    salt site.foo.com web.nginx.restart

The simple target specifications, glob, regex, and list will cover
many use cases, and for some will cover all use cases. There are also
more powerful options.

## Syntax

Basic syntax of targeting client machines is the following:


    [property]:[flags]:<target>

Here `property` is either trait name or inherency key. If you coming
from the Salt world, it would be grain or pillar key respectively.

Flags are the following:

- `r`: Indicates that the `target` is expressed as a regular expression.
- `c`: Makes `target` case-sensitive. By default all targets are _not_
  case sensitive.
- `x`: Inverses the target as "everything except this".
- `a`: Matches everything, invalidates `property` and `target` and is
  equals to `*` (all).
- `i`: Indicates that the `property` is a key to inherency data.

## Simple Matching

To match all clients, use "all" flag or globbing `*`:

```bash
sugar \* system.test.ping
sugar '*' system.test.ping
```

Alternatively, it is much more pleasant to type `:a` or `a:` rather
then escaping an asterisk. Any of the following is just equivalent
to the above:

```bash
sugar :a system.test.ping
sugar a: system.test.ping
sugar :-a: system.test.ping
```

## Globbing Patterns

Simple matching with a bit more flexibility. Let's match all the `webN`
clients in the `example.net` domain (`web1.example.net`,
`web2.example.net`, ... , `webN.example.net`):

```bash
sugar web?.example.net system.test.ping
```

Match the `web1` through `web5` clients:

```bash
sugar web[1-5] system.test.ping
```

Match only `web1` and `web5` clients:

```bash
sugar web[1,5] system.test.ping
```

Match the `web-x`, `web-y`, and `web-z` clients:

```bash
sugar web-[x-z] system.test.ping
```

## List Pattern

List are essentially enumerated values. Each value itself can contain
regular expression or just simple globbing, already explained
above. For example:

```bash
sugar web1,web2,web3 system.test.ping
```

You can also be more specific:

```bash
sugar web[1-3],zoo[1-5],db[1,2] system.test.ping
```

## Regular Expression

clients can be matched using regular expressions, as long as simple
globbing is too mainstream to you. For example, match both `web1-prod`
and `web1-devel` machines:

```bash
sugar :-r:web1-(prod|devel) system.test.ping
```

The flag `-r` (must start with the hyphen) indicates that the
following target expression is a regular expression.

``` important:: Flags must start with the hyphen. Except "a" flag.
```
