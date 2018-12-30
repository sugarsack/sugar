"""
Schema is a library for validating Python data structures, such as those
obtained from config-files, forms, external services or command-line
parsing, converted from JSON/YAML (or something else) to Python data-types.

NOTE: This is a fixed fork of: https://github.com/keleshev/schema
"""

import re
import os

__all__ = ['Schema',
           'And', 'Or', 'Regex', 'Optional', 'Use', 'Forbidden', 'Const',
           'SchemaError',
           'SchemaWrongKeyError',
           'SchemaMissingKeyError',
           'SchemaForbiddenKeyError',
           'SchemaUnexpectedTypeError']


class SchemaError(Exception):
    """
    Error during Schema validation.
    """

    def __init__(self, autos, errors=None):
        self.autos = autos if isinstance(autos, list) else [autos]
        self.errors = errors if isinstance(errors, list) else [errors]
        Exception.__init__(self, self.code)

    @staticmethod
    def uniq(seq):
        """
        Utility function that removes duplicate.
        """
        seen = set()
        return [element for element in seq if element not in seen and not seen.add(element)]

    @property
    def code(self):
        """
        Removes duplicates values in auto and error list.
        parameters.
        """
        data_set = self.uniq(i for i in self.autos if i is not None)
        error_list = self.uniq(i for i in self.errors if i is not None)

        return os.linesep.join(error_list if error_list else data_set)


class SchemaWrongKeyError(SchemaError):
    """
    Error Should be raised when an unexpected key is detected within the
    data set being.
    """


class SchemaMissingKeyError(SchemaError):
    """
    Error should be raised when a mandatory key is not found within the
    data set being validated.
    """


class SchemaForbiddenKeyError(SchemaError):
    """
    Error should be raised when a forbidden key is found within the
    data set being validated, and its value matches the value that was specified.
    """


class SchemaUnexpectedTypeError(SchemaError):
    """
    Error should be raised when a type mismatch is detected within the
    data set being validated.
    """


class And(object):
    """
    Utility function to combine validation directives in AND Boolean fashion.
    """
    def __init__(self, *args, **kw):
        self._args = args
        assert set(kw).issubset(['error', 'schema', 'ignore_extra_keys'])
        self._error = kw.get('error')
        self._ignore_extra_keys = kw.get('ignore_extra_keys', False)
        # You can pass your inherited Schema class.
        self._schema = kw.get('schema', Schema)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join(repr(a) for a in self._args))

    def validate(self, data):
        """
        Validate data using defined sub schema/expressions ensuring all
        values are valid.
        :param data: to be validated with sub defined schemas.
        :return: returns validated data
        """
        for expr in [self._schema(expr, error=self._error,
                                  ignore_extra_keys=self._ignore_extra_keys) for expr in self._args]:
            data = expr.validate(data)
        return data


class Or(And):
    """
    Utility function to combine validation directives in a OR Boolean
    fashion.
    """
    def validate(self, data):
        """
        Validate data using sub defined schema/expressions ensuring at least
        one value is valid.

        :param data: data to be validated by provided schema.
        :return: return validated data if not validation
        """
        autos, errors = [], []
        for stmt in [self._schema(expr, error=self._error,
                                  ignore_extra_keys=self._ignore_extra_keys) for expr in self._args]:
            try:
                return stmt.validate(data)
            except SchemaError as exc:
                autos, errors = exc.autos, exc.errors
        raise SchemaError(['Did not validate %r' % data] + autos,
                          [self._error.format(data) if self._error else None] + errors)


class Regex(object):
    """
    Enables schema.py to validate string using regular expressions.
    """
    # Map all flags bits to a more readable description
    NAMES = ['re.ASCII', 're.DEBUG', 're.VERBOSE', 're.UNICODE', 're.DOTALL',
             're.MULTILINE', 're.LOCALE', 're.IGNORECASE', 're.TEMPLATE']

    def __init__(self, pattern_str, flags=0, error=None):
        self._pattern_str = pattern_str
        flags_list = [Regex.NAMES[i] for i, f in  # Name for each bit
                      enumerate('{0:09b}'.format(flags)) if f != '0']

        if flags_list:
            self._flags_names = ', flags=' + '|'.join(flags_list)
        else:
            self._flags_names = ''

        self._pattern = re.compile(pattern_str, flags=flags)
        self._error = error

    def __repr__(self):
        return '%s(%r%s)' % (self.__class__.__name__, self._pattern_str, self._flags_names)

    def validate(self, data):
        """
        Validated data using defined regex.
        :param data: data to be validated
        :return: return validated data.
        """
        err = self._error
        try:
            if self._pattern.search(data):
                ret = data
            else:
                raise SchemaError('%r does not match %r' % (self, data), err)
        except TypeError:
            raise SchemaError('%r is not string nor buffer' % data, err)

        return ret


class Use(object):
    """
    For more general use cases, you can use the Use class to transform
    the data while it is being validate.
    """
    def __init__(self, callable_, error=None):
        assert callable(callable_)
        self._callable = callable_
        self._error = error

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._callable)

    def validate(self, data):
        """
        Validate object.

        :param data:
        :return:
        """
        try:
            result = self._callable(data)
        except SchemaError as exc:
            raise SchemaError([None] + exc.autos, [self._error.format(data) if self._error else None] + exc.errors)
        except BaseException as exc:
            raise SchemaError('%s(%r) raised %r' % (_callable_str(self._callable), data, exc),
                              self._error.format(data) if self._error else None)
        return result


COMPARABLE, CALLABLE, VALIDATOR, TYPE, DICT, ITERABLE = range(6)


def get_object_priority(obj):
    """
    Return priority for a given object

    :param obj:
    :return:
    """
    if isinstance(obj, (list, tuple, set, frozenset)):
        ret = ITERABLE
    elif isinstance(obj, dict):
        ret = DICT
    elif issubclass(type(obj), type):
        ret = TYPE
    elif hasattr(obj, 'validate'):
        ret = VALIDATOR
    elif callable(obj):
        ret = CALLABLE
    else:
        ret = COMPARABLE

    return ret


class Schema(object):
    """
    Entry point of the library, use this class to instantiate validation
    schema for the data that will be validated.
    """
    def __init__(self, schema, error=None, ignore_extra_keys=False):
        self._schema = schema
        self._error = error
        self._ignore_extra_keys = ignore_extra_keys

    @property
    def scheme(self):
        """
        Get scheme object.

        :return:
        """
        return self._schema

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._schema)

    @staticmethod
    def _dict_key_priority(d_key):
        """
        Return priority for a given key object.

        :param d_key:
        :return:
        """
        if isinstance(d_key, Forbidden):
            ret = get_object_priority(d_key.scheme) - 0.5
        elif isinstance(d_key, Optional):
            ret = get_object_priority(d_key.scheme) + 0.5
        else:
            ret = get_object_priority(d_key)

        return ret

    def is_valid(self, data):
        """
        Return whether the given data has passed all the validations
        that were specified in the given schema.
        """
        try:
            self.validate(data)
        except SchemaError:
            return False
        else:
            return True

    def validate(self, data):
        """
        Validate schema.

        :param data:
        :return:
        """
        schema_class = self.__class__
        schema_data = self._schema
        err_set = self._error
        ign_ex_keys = self._ignore_extra_keys
        flavor = get_object_priority(schema_data)

        if flavor == ITERABLE:
            data = schema_class(type(schema_data), error=err_set).validate(data)
            or_stat = Or(*schema_data, error=err_set, schema=schema_class, ignore_extra_keys=ign_ex_keys)
            return type(data)(or_stat.validate(d) for d in data)

        if flavor == DICT:
            data = schema_class(dict, error=err_set).validate(data)
            new = type(data)()  # new - is a dict of the validated values
            coverage = set()  # matched schema keys
            # for each key and value find a schema entry matching them, if any
            sorted_skeys = sorted(schema_data, key=self._dict_key_priority)
            for key, value in data.items():
                for skey in sorted_skeys:
                    svalue = schema_data[skey]
                    try:
                        nkey = schema_class(skey, error=err_set).validate(key)
                    except SchemaError:
                        pass
                    else:
                        if isinstance(skey, Forbidden):
                            # As the content of the value makes little sense for
                            # forbidden keys, we reverse its meaning:
                            # we will only raise the SchemaErrorForbiddenKey
                            # exception if the value does match, allowing for
                            # excluding a key only if its value has a certain type,
                            # and allowing Forbidden to work well in combination
                            # with Optional.
                            try:
                                nvalue = schema_class(svalue, error=err_set).validate(value)
                            except SchemaError:
                                continue
                            raise SchemaForbiddenKeyError('Forbidden key encountered: %r in %r' % (nkey, data), err_set)
                        else:
                            try:
                                nvalue = schema_class(svalue, error=err_set,
                                                      ignore_extra_keys=ign_ex_keys).validate(value)
                            except SchemaError as exc:
                                msg = "Configuration key '%s' error:" % nkey
                                raise SchemaError([msg] + exc.autos, [err_set] + exc.errors)
                            else:
                                new[nkey] = nvalue
                                coverage.add(skey)
                                break
            required = set(obj for obj in schema_data if not isinstance(obj, (Optional, Forbidden)))

            if not required.issubset(coverage):
                missing_keys = required - coverage
                s_missing_keys = ', '.join(repr(key) for key in sorted(missing_keys, key=repr))
                raise SchemaMissingKeyError('Missing options: ' + s_missing_keys, err_set)

            if not self._ignore_extra_keys and (len(new) != len(data)):
                wrong_keys = set(data.keys()) - set(new.keys())
                s_wrong_keys = ', '.join(repr(key) for key in sorted(wrong_keys, key=repr))
                raise SchemaWrongKeyError('Unexpected option %s in %r' % (s_wrong_keys, data),
                                          err_set.format(data) if err_set else None)

            # Apply default-having optionals that haven't been used:
            defaults = set(key for key in schema_data if isinstance(key, Optional)
                           and hasattr(key, 'default')) - coverage
            for default in defaults:
                new[default.key] = default.default

            return new
        if flavor == TYPE:
            if isinstance(data, schema_data):
                return data
            else:
                raise SchemaUnexpectedTypeError('%r should be type of %r' % (data, schema_data.__name__),
                                                err_set.format(data) if err_set else None)
        if flavor == VALIDATOR:
            try:
                return schema_data.validate(data)
            except SchemaError as exc:
                raise SchemaError([None] + exc.autos, [err_set] + exc.errors)
            except BaseException as exc:
                raise SchemaError('%r.validate(%r) raised %r' % (schema_data, data, exc),
                                  self._error.format(data) if self._error else None)
        if flavor == CALLABLE:
            fnc = _callable_str(schema_data)
            try:
                if schema_data(data):
                    return data
            except SchemaError as exc:
                raise SchemaError([None] + exc.autos, [err_set] + exc.errors)
            except BaseException as exc:
                raise SchemaError('%s(%r) raised %r' % (fnc, data, exc),
                                  self._error.format(data) if self._error else None)
            raise SchemaError('%s(%r) should evaluate to True' % (fnc, data), err_set)
        if schema_data == data:
            return data
        else:
            raise SchemaError('%r does not match %r' % (schema_data, data), err_set.format(data) if err_set else None)


class Optional(Schema):
    """
    Marker for an optional part of the validation Schema.
    """
    _MARKER = object()

    def __init__(self, *args, **kwargs):
        default = kwargs.pop('default', self._MARKER)
        super(Optional, self).__init__(*args, **kwargs)
        if default is not self._MARKER:
            # See if I can come up with a static key to use for myself:
            if get_object_priority(self._schema) != COMPARABLE:
                raise TypeError(
                    'Optional keys with defaults must have simple, '
                    'predictable values, like literal strings or ints. '
                    '"%r" is too complex.' % (self._schema,))
            self.default = default
            self.key = self._schema

    def __hash__(self):
        return hash(self._schema)

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
                getattr(self, 'default', self._MARKER) ==
                getattr(other, 'default', self._MARKER) and
                self._schema == other.scheme)


class Forbidden(Schema):
    """
    Forbidden object.
    """
    def __init__(self, *args, **kwargs):
        super(Forbidden, self).__init__(*args, **kwargs)
        self.key = self._schema


class Const(Schema):
    """
    Constant object.
    """
    def validate(self, data):
        super(Const, self).validate(data)
        return data


def _callable_str(callable_object):
    """
    Get a name of the callable object.

    :param callable_object:
    :return:
    """
    return callable_object.__name__ if hasattr(callable_object, '__name__') else str(callable_object)
