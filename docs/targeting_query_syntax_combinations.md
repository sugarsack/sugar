# Targeting Clients (Advanced)

Sugar allows target clients in more granular way using inherencies and
traits. From the previous chapter you already learned the following
syntax:

```bash
[property]:[flags]:<target>
```

To recap:

- **"Property"** is what one would refer as "key" in a structure or
  dictionary. This section is _optional_.
- **"Flags"** is used to select _what kind of_ property is used:
  inherency or trait etc. This section is _optional_.
- **"target"** is what one would refer as "value" in a structure or
  dictionary. This section is _required_.

## Operators: `AND`, `OR`

You can join matcher within your query with `and` and `or`
operators. To use `not` operator you should set a flag to a matcher
that inverts its match turning `and` to `and not ...` as well as `or`
to `or not ...`.

### Joining with `AND` operator

To join any subsequent matcher into one chain with `and` operator, use
`/` (slash) or `&&` or just ` and ` with spaces around. The following
examples are equally same:

<div class="highlight">
<pre>
<span class="c1">&lt;first&gt;</span><b class="s1">/</b><span class="c1">&lt;second&gt;</span>
<span class="c1">&lt;first&gt;</span><b class="s1">&&</b><span class="c1">&lt;second&gt;</span>
<span class="c1">&lt;first&gt;</span><b class="s1"> and </b><span class="c1">&lt;second&gt;</span>
</pre>
</div>

In this case _"second"_ expression will be picking up from the result
that was returned by _"first"_ expression and resulting set will be in
use.

### Joining with `OR` operator

The `or` operator works between blocks over the entire set of known
machines. To join set of `and`-joined matchers or standalone matchers
with `or` operator, use `//` (double-slash), `||` or just ` or ` with
spaces around. The following examples are equally same:

<div class="highlight">
<pre>
<span class="c1">&lt;first&gt;</span><b class="s1">//</b><span class="c1">&lt;second&gt;</span>
<span class="c1">&lt;first&gt;</span><b class="s1">||</b><span class="c1">&lt;second&gt;</span>
<span class="c1">&lt;first&gt;</span><b class="s1"> or </b><span class="c1">&lt;second&gt;</span>
</pre>
</div>

Here _"second"_ expression will be picking from the same original
source as _"first"_, and then both results will be combined together.

``` important:: Spaces are required around only "and" and "or" operators. Otherwise they are optional for just better readability.
```

### Ugh... Slashes are odd here!

Yes. But they are also _easier to type_. So for exactly the same
reasons as you would write on of the following (possibly mistyping `*`
as `&` or `(` accidentally or pressing ENTER key instead of `'` on
English standard keyboard):

```bash
sugar \* ....
sugar '*' ....
```

Instead of above, you can also write the same this way:


```bash
sugar :a ....
```

It just only feels more handy and safe to type. The same happens with
slashes versus `||` and `&&` (requires Shift involved): slash is just
right there!

In any case, all this is optional, you can choose any syntax you like.

### Invert results with `NOT` operator

To invert something, use `x` flag:

<div class="highlight">
<pre>
<span class="c1"><b class="s1">:x:</b><span class="c1">&lt;expression&gt;</span>
</pre>
</div>

In this case the result of the _"expression"_ will be inverted. For
example, match all systems but `foo`:

```bash
sugar ':x:foo' system.test.ping
```

Please note here that flag `:x:foo` starts with the colon `:`. In this
case Sugar interprets `x` as an inversion flag. However, if the
expression would be `x:foo`, then `x` would be interpreted as a
property name `x` and target `foo` where flags are undefined.

``` important:: Flags must beging with colon, otherwise Sugar will interpret them as property name.
```

## Examples

This example is using all three ways of writing logical operators. All
further examples will use slashes-based syntax.

The following string matches all Debian clients with a hostname that
begins with `webserv`, as well as any machines that have a hostname
which matches the regular expression `web-dc1-srv.*`:

```bash
sugar 'webserv* / os:debian // web-dc1-srv.*' system.test.ping
sugar 'webserv* && os:debian || web-dc1-srv.*' system.test.ping
sugar 'webserv* and os:debian or web-dc1-srv.*' system.test.ping
```

Spaces between logical operators might be omitted, except `and` and
`or` ones.

Inversion works through the flag `x`. So in order to exclude a client
hostname (ping all machines, except `web-dc1-srv`):

```bash
sugar :x:web-dc1-srv system.test.ping
```

## Verifying query

Sugar can also read for you your own query in English, explaining what
you are trying to target. For example this very long query can be
explained by Sugar for you:

```bash
sugar '*.example.org,*.sugarsack.org,*.domain.com/:-x:*[1-3]*//zoo[1-3]/:-x:zoo[3]' --explain
```

This prints the following message:

```text
Match clients where target is a reg-exp
'(.*\.example\.org\Z(?ms)|.*\.sugarsack\.org\Z(?ms)|.*\.domain\.com\Z(?ms))'
and where target is an inversion of '*[1-3]*' or where target is
globbing of 'zoo[1-3]' and where target is an inversion of 'zoo[3]'.
```
