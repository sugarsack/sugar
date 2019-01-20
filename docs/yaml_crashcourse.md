# YAML Crash Course

If you are new to YAML or you already used it but stuck with
something, here is a simple crash-course for you to learn it in just
no time.

```important:: The entire YAML document is a map.
```
From the moment you started writing YAML, you're started writing a
**map**. In Java it is like "HashMap", in Python it is "dict", in
Perl "hash", in C "struct" etc.

## Scalar

A simple dictionary of a key/value:

```yaml
some_key: some_value
```

Let's do this again:

```yaml
some_key: some_value
some_more_key: some_other_value
a_number: 100
scientific_number: 2e+11
or_just_so: 200000000000.0
also_number: 1
```

### More on keys

Keys in YAML can have spaces, like so:

```yaml
some key with the spaces: data`
```

Keys can be also multi-line, e.g.:

```yaml
? |
  In this key we have
  multiple lines
: "This string is its value and is quoted, but doesn't have to be so"
```

While YAML _can_ support sequences in the keys, it won't work for
Sugar. The problem is that in Python mapping all keys are
immutable. So while below is purely valid YAML, it will not be
accepted in Sugar:

```yaml
? - foo
  - bar
: [one, two]
```

It, of course possible to rewrite and Sugar will take it, by forcing
immutable tuple key. In this case Python will replace list with a
tuple and it will work:

```yaml
!!python/tuple [foo, bar]: [one, two]
```

However, again, Sugar does not have any use of this.


### Strings (single-line)
Usually strings aren't quoted, you _just_ write them as above. But you
can also quote them `'quoted like this'`, if you want or this is
needed. This is valid for keys and values, e.g.:

```yaml
'quoted key': "double-quotes, because 'this' was single-quoted"
sometimes: 'you can quote twice ''like this'' in the string value'
double quotes: "are perfectly used as well"
```

Quotes can be also escaped:

```yaml
key: "Some \"special\" value"
```

### String (forced)

You may also force string type by tagging specific value:

```yaml
key: !!str 15
```

This is also handy if your YAML template is also Jinja2 template. So you
are not sure what will be returned here:

```yaml
key: {{ variable }}
```

In this case you can force it being a string:

```yaml
key: !!str {{ variable }}
```

### More on special characters

You can also add some special characters with the escape:

```yaml
some key: "inside here is: \", \0, \t, \u263A, \x0d\x0a \r \n some stuff"
```

### Strings (multi-line)

Such strings can be written either as a 'literal block' by using `|`
symbol, like so:

```yaml
foo: |
   This text block is the value of `foo` key, while line breaks are
   fully preserved. This leading identation doesn't count and will be
   completely removed.

      However, this identation is four spaces away and will be
      preserved. Same as the line breaks.

```

Another way of write multi-line block is using folding, through the
symbol `>`. The difference between above is that to make a new line,
you will need to add an extra blank line. Otherwise all newlines will
be replaces with one space.

```yaml
foo: >
    In the `folded style` this current sentence will be just one line
	without any newlines. This second sentence will be also in the
	same line as previous.

    And since now here is one extra blank line, this line will be
    finally the new one.
```

## Boolean

If you want it real _boolean_, you should write it as `true` or
`false`. If you write it as `1` or `0`, you will get a _number_ type
of `1` and `0` respectively:

```yaml
yes: true
no: false
```

## Date and time

Date/time if in ISO 8601, gets automatically parsed into a datetime object:

```yaml
datetime: 2019-02-01T01:45:28.6Z
datetime_with_spaces: 2019-02-01 20:30:45.13 -5
date: 2019-02-15
```

## Null values

Null values are defined in YAML in both ways:

- As `null` keyword.
- As nothing.

For example:

```yaml
key:
other_key: null
```

Both will have null values. If you write something like `nil` or
`None` it will be just a string of `"nil"` or `"None"` respectively.

## Sequences

Sequences in YAML starts with `-` (minus) symbol, like so:

```yaml
some_key:
  - item 1
  - item 2
  - and
  - so
  - on..
```

It does not matte what type you are putting into the sequence:

```yaml
some_key:
  - some string
  - null
  - true
  - 0.1
  - "whatever else"

```

### Nested sequences

What happens if you want to have a map with a scalar inside, another
map and a sequences? The syntax gets a bit more complicated. But it is
still possible:

```yaml
some_key_name:
  - item 1
  - item 2
  - nested_key: "nested value"
    another_nested_key: "another nested value"
  -
    - nested item 1
    - nested item 2
  - - - even deeper nested item 1
      - even deeper nested item 2
```

In the example above, the minus `-` symbol is used also as
indentation. Note an empty `-` after `another_nested_key`. It starts a
sequence after.

## Sets

YAML does support sets. Set is basically what map/keys returns (or map with
keys and `null` values). They are declared as so:

```yaml
this is a set:
  ? key1
  ? key2
  ? key3
```

It is also possible to just use JSON format (but better don't):

```yaml
this is a set: {key1, key2, key3}
```

The same effect is to declare a map with `null` values (either write `null`
explicitly or just omit it:

```yaml
this is a set:
  key1:
  key2:
  key3:

```

## You can, but don't

Since YAML is just a superset of JSON, you can happily embed JSON into
a YAML (and thus make it look ugly):

```yaml
some_map: {"key": "value"}
some_sequence: ["let", "just", "make", "it", "unreadable"]
or even so: {stuff: ["that", "looks"], like: Perl}
```

## Inheritance

YAML can inherit data. This is very handly if there is something in the
structure that would is perfectly to be reused and you do not want to 
re/write it all over again. In this case it is possible to just inherit
that part, like so:


```yaml
key: &label This value will be repeated in key1
key1: *label

```

The "label" (or an anchor) normally is written as same as the key, so
then it is easier to remember or find out what it refers to. With the
anchor you mark a block that is inheritable, like so:

```yaml
main: &main
  key: value
```

In the example above, the _content_ of the `main` will be included elsewhere,
as long as you request it:

```yaml
foo &foo:
  <<: *main
  second_key: value
  
bar &bar:
  <<: *main
  second_key: some other value
```

In this case `foo` and `bar` will have also `key: value` pair included. Then
it is also possible to inherit multiple blocks:

```yaml
everything:
  is: awesome
  <<: *foo
  <<: *bar

```
