# -*- coding: utf-8 -*-
"""
Functions for manipulating, inspecting, or otherwise working with data types
and data structures.
"""

# NOTE: This code is taken from Salt and should be cleaned up on demand.
#       Not everything is used here, many parts do not even need to exist.
#       Therefore many crucial pylint checks are simply disabled not to waste
#       time on something that might be even not really needed.
#       However, if you are touching something related and using it, please
#       Remove pylint block and refactor the code accordingly!

from __future__ import absolute_import, print_function, unicode_literals

# Import Python libs
import fnmatch
import logging
import re

from sugar.lib.compat import CollectionsMapping as Mapping
from sugar.lib import six
from sugar.utils import stringutils

try:
    import jmespath
except ImportError:
    jmespath = None

log = logging.getLogger(__name__)  # pylint: disable=C0103


DEFAULT_TARGET_DELIMETER = ":"


def compare_dicts(old=None, new=None):
    """
    Compare before and after results from various salt functions, returning a
    dict describing the changes that were made.

    :param old: old dict
    :param new: new dict
    :return: dict
    """
    ret = {}
    for key in set((new or {})).union((old or {})):
        if key not in old:
            # New key
            ret[key] = {'old': '',
                        'new': new[key]}
        elif key not in new:
            # Key removed
            ret[key] = {'new': '',
                        'old': old[key]}
        elif new[key] != old[key]:
            # Key modified
            ret[key] = {'old': old[key],
                        'new': new[key]}
    return ret


def compare_lists(old=None, new=None):
    """
    Compare before and after results from various salt functions, returning a
    dict describing the changes that were made

    :param old: list, default None
    :param new: list, default None
    :return: dictionary
    """
    ret = dict()
    for item in new:
        if item not in old:
            ret['new'] = item
    for item in old:
        if item not in new:
            ret['old'] = item
    return ret


def decode(data, encoding=None, errors='strict', keep=False,
           normalize=False, preserve_dict_class=False, preserve_tuples=False,
           to_str=False):
    """
    Generic function which will decode whichever type is passed, if necessary.
    Optionally use to_str=True to ensure strings are str types and not unicode
    on Python 2.

    If `strict` is True, and `keep` is False, and we fail to decode, a
    UnicodeDecodeError will be raised. Passing `keep` as True allows for the
    original value to silently be returned in cases where decoding fails. This
    can be useful for cases where the data passed to this function is likely to
    contain binary blobs, such as in the case of cp.recv.

    If `normalize` is True, then unicodedata.normalize() will be used to
    normalize unicode strings down to a single code point per glyph. It is
    recommended not to normalize unless you know what you're doing. For
    instance, if `data` contains a dictionary, it is possible that normalizing
    will lead to data loss because the following two strings will normalize to
    the same value:

    - u'\\u044f\\u0438\\u0306\\u0446\\u0430.txt'
    - u'\\u044f\\u0439\\u0446\\u0430.txt'

    One good use case for normalization is in the test suite. For example, on
    some platforms such as Mac OS, os.listdir() will produce the first of the
    two strings above, in which "й" is represented as two code points (i.e. one
    for the base character, and one for the breve mark). Normalizing allows for
    a more reliable test case.

    :param data: data to work with
    :param encoding: default encoding
    :param errors: errors to process with
    :param keep: bool
    :param normalize: bool
    :param preserve_dict_class: bool
    :param preserve_tuples: bool
    :param to_str: bool
    :return: decoded data
    """
    _decode_func = stringutils.to_unicode if not to_str else stringutils.to_str
    if isinstance(data, Mapping):
        ret = decode_dict(data, encoding, errors, keep, normalize, preserve_dict_class, preserve_tuples, to_str)
    elif isinstance(data, list):
        ret = decode_list(data, encoding, errors, keep, normalize, preserve_dict_class, preserve_tuples, to_str)
    elif isinstance(data, tuple):
        ret = (decode_tuple(data, encoding, errors, keep, normalize, preserve_dict_class, to_str)
               if preserve_tuples else decode_list(data, encoding, errors, keep, normalize,
                                                   preserve_dict_class, preserve_tuples, to_str))
    else:
        try:
            data = _decode_func(data, encoding, errors, normalize)
        except TypeError:
            # to_unicode raises a TypeError when input is not a
            # string/bytestring/bytearray. This is expected and simply means we
            # are going to leave the value as-is.
            pass
        except UnicodeDecodeError:
            if not keep:
                raise
        ret = data

    return ret


def decode_dict(data, encoding=None, errors='strict', keep=False,
                normalize=False, preserve_dict_class=False,
                preserve_tuples=False, to_str=False):
    """
    Decode all string values to Unicode. Optionally use to_str=True to ensure
    strings are str types and not unicode on Python 2.

    :param data: data to work with
    :param encoding: default encoding
    :param errors: errors to process with
    :param keep: bool
    :param normalize: bool
    :param preserve_dict_class: bool
    :param preserve_tuples: bool
    :param to_str: bool
    :return: decoded data
    """
    _decode_func = stringutils.to_unicode if not to_str else stringutils.to_str
    # Make sure we preserve OrderedDicts
    rv_dt = data.__class__() if preserve_dict_class else {}
    for key, value in six.iteritems(data):
        if isinstance(key, tuple):
            key = (decode_tuple(key, encoding, errors, keep, normalize, preserve_dict_class, to_str)
                   if preserve_tuples else decode_list(key, encoding, errors, keep, normalize,
                                                       preserve_dict_class, preserve_tuples, to_str))
        else:
            try:
                key = _decode_func(key, encoding, errors, normalize)
            except TypeError:
                # to_unicode raises a TypeError when input is not a
                # string/bytestring/bytearray. This is expected and simply
                # means we are going to leave the value as-is.
                pass
            except UnicodeDecodeError:
                if not keep:
                    raise

        if isinstance(value, list):
            value = decode_list(value, encoding, errors, keep, normalize,
                                preserve_dict_class, preserve_tuples, to_str)
        elif isinstance(value, tuple):
            value = (decode_tuple(value, encoding, errors, keep, normalize, preserve_dict_class, to_str)
                     if preserve_tuples else decode_list(value, encoding, errors, keep, normalize,
                                                         preserve_dict_class, preserve_tuples, to_str))
        elif isinstance(value, Mapping):
            value = decode_dict(value, encoding, errors, keep, normalize,
                                preserve_dict_class, preserve_tuples, to_str)
        else:
            try:
                value = _decode_func(value, encoding, errors, normalize)
            except TypeError:
                # to_unicode raises a TypeError when input is not a
                # string/bytestring/bytearray. This is expected and simply
                # means we are going to leave the value as-is.
                pass
            except UnicodeDecodeError:
                if not keep:
                    raise
        rv_dt[key] = value

    return rv_dt


# pylint: disable=R1705,R0911,R0912,R0915
def decode_list(data, encoding=None, errors='strict', keep=False,
                normalize=False, preserve_dict_class=False,
                preserve_tuples=False, to_str=False):
    """
    Decode all string values to Unicode. Optionally use to_str=True to ensure
    strings are str types and not unicode on Python 2.

    :param data: data to work with
    :param encoding: default encoding
    :param errors: errors to process with
    :param keep: bool
    :param normalize: bool
    :param preserve_dict_class: bool
    :param preserve_tuples: bool
    :param to_str: bool
    :return: decoded data
    """
    _decode_func = stringutils.to_unicode if not to_str else stringutils.to_str
    ret = []
    for item in data:
        if isinstance(item, list):
            item = decode_list(item, encoding, errors, keep, normalize,
                               preserve_dict_class, preserve_tuples, to_str)
        elif isinstance(item, tuple):
            item = (decode_tuple(item, encoding, errors, keep, normalize, preserve_dict_class, to_str)
                    if preserve_tuples else decode_list(item, encoding, errors, keep, normalize,
                                                        preserve_dict_class, preserve_tuples, to_str))
        elif isinstance(item, Mapping):
            item = decode_dict(item, encoding, errors, keep, normalize,
                               preserve_dict_class, preserve_tuples, to_str)
        else:
            try:
                item = _decode_func(item, encoding, errors, normalize)
            except TypeError:
                # to_unicode raises a TypeError when input is not a
                # string/bytestring/bytearray. This is expected and simply
                # means we are going to leave the value as-is.
                pass
            except UnicodeDecodeError:
                if not keep:
                    raise
        ret.append(item)

    return ret
# pylint: enable=R1705,R0911,R0912,R0915


def decode_tuple(data, encoding=None, errors='strict', keep=False,
                 normalize=False, preserve_dict_class=False, to_str=False):
    """
    Decode all string values to Unicode. Optionally use to_str=True to ensure
    strings are str types and not unicode on Python 2.

    :param data: data to work with
    :param encoding: default encoding
    :param errors: errors to process with
    :param keep: bool
    :param normalize: bool
    :param preserve_dict_class: bool
    :param to_str: bool
    :return: decoded data
    """
    return tuple(
        decode_list(data, encoding, errors, keep, normalize,
                    preserve_dict_class, True, to_str)
    )


# pylint: disable=R1705,R0911,R0912,R0915
def encode(data, encoding=None, errors='strict', keep=False,
           preserve_dict_class=False, preserve_tuples=False):
    """
    Generic function which will encode whichever type is passed, if necessary

    If `strict` is True, and `keep` is False, and we fail to encode, a
    UnicodeEncodeError will be raised. Passing `keep` as True allows for the
    original value to silently be returned in cases where encoding fails. This
    can be useful for cases where the data passed to this function is likely to
    contain binary blobs.

    :param data: data to work with
    :param encoding: default encoding
    :param errors: errors to process with
    :param keep: bool
    :param preserve_dict_class: bool
    :param preserve_tuples: bool
    :return: encoded data
    """
    if isinstance(data, Mapping):
        return encode_dict(data, encoding, errors, keep,
                           preserve_dict_class, preserve_tuples)
    elif isinstance(data, list):
        return encode_list(data, encoding, errors, keep,
                           preserve_dict_class, preserve_tuples)
    elif isinstance(data, tuple):
        return (encode_tuple(data, encoding, errors, keep, preserve_dict_class)
                if preserve_tuples else encode_list(data, encoding, errors, keep, preserve_dict_class, preserve_tuples))
    else:
        try:
            return stringutils.to_bytes(data, encoding, errors)
        except TypeError:
            # to_bytes raises a TypeError when input is not a
            # string/bytestring/bytearray. This is expected and simply
            # means we are going to leave the value as-is.
            pass
        except UnicodeEncodeError:
            if not keep:
                raise
        return data
# pylint: enable=R1705,R0911,R0912,R0915


# pylint: disable=R1705,R0911,R0912,R0915
def encode_dict(data, encoding=None, errors='strict', keep=False,
                preserve_dict_class=False, preserve_tuples=False):
    """
    Encode all string values to bytes

    :param data: data to work with
    :param encoding: default encoding
    :param errors: errors to process with
    :param keep: bool
    :param preserve_dict_class: bool
    :param preserve_tuples: bool
    :return: encoded data
    """
    ret = data.__class__() if preserve_dict_class else {}
    for key, value in six.iteritems(data):
        if isinstance(key, tuple):
            key = (encode_tuple(key, encoding, errors, keep, preserve_dict_class)
                   if preserve_tuples else encode_list(key, encoding, errors, keep,
                                                       preserve_dict_class, preserve_tuples))
        else:
            try:
                key = stringutils.to_bytes(key, encoding, errors)
            except TypeError:
                # to_bytes raises a TypeError when input is not a
                # string/bytestring/bytearray. This is expected and simply
                # means we are going to leave the value as-is.
                pass
            except UnicodeEncodeError:
                if not keep:
                    raise

        if isinstance(value, list):
            value = encode_list(value, encoding, errors, keep,
                                preserve_dict_class, preserve_tuples)
        elif isinstance(value, tuple):
            value = (encode_tuple(value, encoding, errors, keep, preserve_dict_class)
                     if preserve_tuples else encode_list(value, encoding, errors, keep,
                                                         preserve_dict_class, preserve_tuples))
        elif isinstance(value, Mapping):
            value = encode_dict(value, encoding, errors, keep,
                                preserve_dict_class, preserve_tuples)
        else:
            try:
                value = stringutils.to_bytes(value, encoding, errors)
            except TypeError:
                # to_bytes raises a TypeError when input is not a
                # string/bytestring/bytearray. This is expected and simply
                # means we are going to leave the value as-is.
                pass
            except UnicodeEncodeError:
                if not keep:
                    raise

        ret[key] = value
    return ret
# pylint: enable=R1705,R0911,R0912,R0915


def encode_list(data, encoding=None, errors='strict', keep=False,
                preserve_dict_class=False, preserve_tuples=False):
    """
    Encode all string values to bytes

    :param data: data to work with
    :param encoding: default encoding
    :param errors: errors to process with
    :param keep: bool
    :param preserve_dict_class: bool
    :param preserve_tuples: bool
    :return: encoded list
    """
    ret = []
    for item in data:
        if isinstance(item, list):
            item = encode_list(item, encoding, errors, keep, preserve_dict_class, preserve_tuples)
        elif isinstance(item, tuple):
            item = (encode_tuple(item, encoding, errors, keep, preserve_dict_class) if preserve_tuples
                    else encode_list(item, encoding, errors, keep, preserve_dict_class, preserve_tuples))
        elif isinstance(item, Mapping):
            item = encode_dict(item, encoding, errors, keep, preserve_dict_class, preserve_tuples)
        else:
            try:
                item = stringutils.to_bytes(item, encoding, errors)
            except TypeError:
                # to_bytes raises a TypeError when input is not a
                # string/bytestring/bytearray. This is expected and simply
                # means we are going to leave the value as-is.
                pass
            except UnicodeEncodeError:
                if not keep:
                    raise

        ret.append(item)
    return ret


def encode_tuple(data, encoding=None, errors='strict', keep=False,
                 preserve_dict_class=False):
    """
    Encode all string values to Unicode

    :param data: data to work with
    :param encoding: default encoding
    :param errors: errors to process with
    :param keep: bool
    :param preserve_dict_class: bool
    :return: encoded tuple
    """
    return tuple(
        encode_list(data, encoding, errors, keep, preserve_dict_class, True))


def exactly_n(lst, num=1):
    """
    Tests that exactly N items in an iterable are "truthy"
    (neither None, False, nor 0).

    :param lst: iterable (list)
    :param num: truth number
    :return: bool
    """
    idx = iter(lst)
    return all(any(idx) for _ in range(num)) and not any(idx)


def exactly_one(lst):
    """
    Check if only one item is not None, False, or 0 in an iterable.

    :param lst: list
    :returns: bool
    """
    return exactly_n(lst)


# def filter_by(lookup_dict,
#               lookup,
#               traverse,
#               merge=None,
#               default='default',
#               base=None):
#     """
#     Common code to filter data structures like grains and pillar
#     """
#     ret = None
#     # Default value would be an empty list if lookup not found
#     val = traverse_dict_and_list(traverse, lookup, [])
#
#     # Iterate over the list of values to match against patterns in the
#     # lookup_dict keys
#     for each in val if isinstance(val, list) else [val]:
#         for key in lookup_dict:
#             test_key = key if isinstance(key, six.string_types) \
#                 else six.text_type(key)
#             test_each = each if isinstance(each, six.string_types) \
#                 else six.text_type(each)
#             if fnmatch.fnmatchcase(test_each, test_key):
#                 ret = lookup_dict[key]
#                 break
#         if ret is not None:
#             break
#
#     if ret is None:
#         ret = lookup_dict.get(default, None)
#
#     if base and base in lookup_dict:
#         base_values = lookup_dict[base]
#         if ret is None:
#             ret = base_values
#
#         elif isinstance(base_values, Mapping):
#             if not isinstance(ret, Mapping):
#                 raise exceptions.SugarException(
#                     'filter_by default and look-up values must both be '
#                     'dictionaries.')
#             ret = salt.utils.dictupdate.update(copy.deepcopy(base_values), ret)
#
#     if merge:
#         if not isinstance(merge, Mapping):
#             raise exceptions.SugarException(
#                 'filter_by merge argument must be a dictionary.')
#
#         if ret is None:
#             ret = merge
#         else:
#             salt.utils.dictupdate.update(ret, copy.deepcopy(merge))
#
#     return ret


def traverse_dict(data, key, default=None, delimiter=DEFAULT_TARGET_DELIMETER):
    """
    Traverse a dict using a colon-delimited (or otherwise delimited, using the
    'delimiter' param) target string. The target 'foo:bar:baz' will return
    data['foo']['bar']['baz'] if this value exists, and will otherwise return
    the dict in the default argument.

    :param data: dictionary data
    :param key: key to traverse of
    :param default: default is None
    :param delimiter: path delimeter, detault is DEFAULT_TARGET_DELIMETER (":")
    :return: pointer to the data
    """
    ptr = data
    try:
        for each in key.split(delimiter):
            ptr = ptr[each]
    except (KeyError, IndexError, TypeError):
        # Encountered a non-indexable value in the middle of traversing
        ptr = default

    return ptr


# pylint: disable=R1705,R0911,R0912,R0915
def traverse_dict_and_list(data, key, default=None, delimiter=DEFAULT_TARGET_DELIMETER):
    """
    Traverse a dict or list using a colon-delimited (or otherwise delimited,
    using the 'delimiter' param) target string. The target 'foo:bar:0' will
    return data['foo']['bar'][0] if this value exists, and will otherwise
    return the dict in the default argument.
    Function will automatically determine the target type.
    The target 'foo:bar:0' will return data['foo']['bar'][0] if data like
    {'foo':{'bar':['baz']}} , if data like {'foo':{'bar':{'0':'baz'}}}
    then return data['foo']['bar']['0']

    :param data: dictionary or list data
    :param key: key to traverse of
    :param default: default is None
    :param delimiter: path delimeter, detault is DEFAULT_TARGET_DELIMETER (":")
    :return: pointer to the data
    """
    ptr = data
    for each in key.split(delimiter):
        if isinstance(ptr, list):
            try:
                idx = int(each)
            except ValueError:
                embed_match = False
                # Index was not numeric, lets look at any embedded dicts
                for embedded in (x for x in ptr if isinstance(x, dict)):
                    try:
                        ptr = embedded[each]
                        embed_match = True
                        break
                    except KeyError:
                        pass
                if not embed_match:
                    # No embedded dicts matched, return the default
                    return default
            else:
                try:
                    ptr = ptr[idx]
                except IndexError:
                    return default
        else:
            try:
                ptr = ptr[each]
            except (KeyError, TypeError):
                return default
    return ptr
# pylint: enable=R1705,R0911,R0912,R0915


# pylint: disable=R1705,R0911,R0912,R0915
def subdict_match(data, expr, delimiter=DEFAULT_TARGET_DELIMETER,
                  regex_match=False, exact_match=False):
    """
    Check for a match in a dictionary using a delimiter character to denote
    levels of subdicts, and also allowing the delimiter character to be
    matched. Thus, 'foo:bar:baz' will match data['foo'] == 'bar:baz' and
    data['foo']['bar'] == 'baz'. The latter would take priority over the
    former, as more deeply-nested matches are tried first.

    :param data: data to work with
    :param expr: expression to match
    :param delimiter: path delimeter
    :param regex_match: bool
    :param exact_match: bool
    :return: bool
    """
    def _match(target, pattern, regex_match=False, exact_match=False):
        # The reason for using six.text_type first and _then_ using
        # to_unicode as a fallback is because we want to eventually have
        # unicode types for comparison below. If either value is numeric then
        # six.text_type will turn it into a unicode string. However, if the
        # value is a PY2 str type with non-ascii chars, then the result will be
        # a UnicodeDecodeError. In those cases, we simply use to_unicode to
        # decode it to unicode. The reason we can't simply use to_unicode to
        # begin with is that (by design) to_unicode will raise a TypeError if a
        # non-string/bytestring/bytearray value is passed.
        try:
            target = six.text_type(target).lower()
        except UnicodeDecodeError:
            target = stringutils.to_unicode(target).lower()
        try:
            pattern = six.text_type(pattern).lower()
        except UnicodeDecodeError:
            pattern = stringutils.to_unicode(pattern).lower()

        if regex_match:
            try:
                return re.match(pattern, target)
            except Exception:
                log.error('Invalid regex \'%s\' in match', pattern)
                return False
        else:
            return target == pattern if exact_match else fnmatch.fnmatch(target, pattern)

    def _dict_match(target, pattern, regex_match=False, exact_match=False):
        wildcard = pattern.startswith('*:')
        if wildcard:
            pattern = pattern[2:]

        if pattern == '*':
            # We are just checking that the key exists
            return True
        elif pattern in target:
            # We might want to search for a key
            return True
        elif subdict_match(target,
                           pattern,
                           regex_match=regex_match,
                           exact_match=exact_match):
            return True
        if wildcard:
            for key in target:
                if isinstance(target[key], dict):
                    if _dict_match(target[key],
                                   pattern,
                                   regex_match=regex_match,
                                   exact_match=exact_match):
                        return True
                elif isinstance(target[key], list):
                    for item in target[key]:
                        if _match(item,
                                  pattern,
                                  regex_match=regex_match,
                                  exact_match=exact_match):
                            return True
                elif _match(target[key],
                            pattern,
                            regex_match=regex_match,
                            exact_match=exact_match):
                    return True
        return False

    splits = expr.split(delimiter)
    num_splits = len(splits)
    if num_splits == 1:
        # Delimiter not present, this can't possibly be a match
        return False

    splits = expr.split(delimiter)
    num_splits = len(splits)
    if num_splits == 1:
        # Delimiter not present, this can't possibly be a match
        return False

    # If we have 4 splits, then we have three delimiters. Thus, the indexes we
    # want to use are 3, 2, and 1, in that order.
    for idx in range(num_splits - 1, 0, -1):
        key = delimiter.join(splits[:idx])
        if key == '*':
            # We are matching on everything under the top level, so we need to
            # treat the match as the entire data being passed in
            matchstr = expr
            match = data
        else:
            matchstr = delimiter.join(splits[idx:])
            match = traverse_dict_and_list(data, key, {}, delimiter=delimiter)
        log.debug("Attempting to match '%s' in '%s' using delimiter '%s'",
                  matchstr, key, delimiter)
        if match == {}:
            continue
        if isinstance(match, dict):
            if _dict_match(match,
                           matchstr,
                           regex_match=regex_match,
                           exact_match=exact_match):
                return True
            continue
        if isinstance(match, (list, tuple)):
            # We are matching a single component to a single list member
            for member in match:
                if isinstance(member, dict):
                    if _dict_match(member,
                                   matchstr,
                                   regex_match=regex_match,
                                   exact_match=exact_match):
                        return True
                if _match(member,
                          matchstr,
                          regex_match=regex_match,
                          exact_match=exact_match):
                    return True
            continue
        if _match(match,
                  matchstr,
                  regex_match=regex_match,
                  exact_match=exact_match):
            return True
    return False
# pylint: enable=R1705,R0911,R0912,R0915


def substr_in_list(string_to_search_for, list_to_search):
    """
    Return a boolean value that indicates whether or not a given
    string is present in any of the strings which comprise a list

    :param string_to_search_for: string to search
    :param list_to_search: list to search
    :return: str
    """
    return any(string_to_search_for in s for s in list_to_search)


def is_dictlist(data):
    """
    Returns True if data is a list of one-element dicts (as found in many SLS
    schemas), otherwise returns False

    :param data: data to check
    :return: bool
    """

    is_one_element = False
    if isinstance(data, list):
        for element in data:
            if isinstance(element, dict):
                is_one_element = len(element) == 1
                if not is_one_element:
                    break
            else:
                break

    return is_one_element


# def repack_dictlist(data,
#                     strict=False,
#                     recurse=False,
#                     key_cb=None,
#                     val_cb=None):
#     """
#     Takes a list of one-element dicts (as found in many SLS schemas) and
#     repacks into a single dictionary.
#     """
#     if isinstance(data, six.string_types):
#         try:
#             data = salt.utils.yaml.safe_load(data)
#         except salt.utils.yaml.parser.ParserError as err:
#             log.error(err)
#             return {}
#
#     if key_cb is None:
#         key_cb = lambda x: x
#     if val_cb is None:
#         val_cb = lambda x, y: y
#
#     valid_non_dict = (six.string_types, six.integer_types, float)
#     if isinstance(data, list):
#         for element in data:
#             if isinstance(element, valid_non_dict):
#                 continue
#             elif isinstance(element, dict):
#                 if len(element) != 1:
#                     log.error(
#                         'Invalid input for repack_dictlist: key/value pairs '
#                         'must contain only one element (data passed: %s).',
#                         element
#                     )
#                     return {}
#             else:
#                 log.error(
#                     'Invalid input for repack_dictlist: element %s is '
#                     'not a string/dict/numeric value', element
#                 )
#                 return {}
#     else:
#         log.error(
#             'Invalid input for repack_dictlist, data passed is not a list '
#             '(%s)', data
#         )
#         return {}
#
#     ret = {}
#     for element in data:
#         if isinstance(element, valid_non_dict):
#             ret[key_cb(element)] = None
#         else:
#             key = next(iter(element))
#             val = element[key]
#             if is_dictlist(val):
#                 if recurse:
#                     ret[key_cb(key)] = repack_dictlist(val, recurse=recurse)
#                 elif strict:
#                     log.error(
#                         'Invalid input for repack_dictlist: nested dictlist '
#                         'found, but recurse is set to False'
#                     )
#                     return {}
#                 else:
#                     ret[key_cb(key)] = val_cb(key, val)
#             else:
#                 ret[key_cb(key)] = val_cb(key, val)
#     return ret


def is_list(value):
    """
    Check if a variable is a list.

    :param value: object
    :returns: bool
    """
    return isinstance(value, list)


def is_iter(data, ignore=six.string_types):
    """
    Test if an object is iterable, but not a string type.

    Test if an object is an iterator or is iterable itself. By default this
    does not return True for string objects.

    The `ignore` argument defaults to a list of string types that are not
    considered iterable. This can be used to also exclude things like
    dictionaries or named tuples.

    Based on https://bitbucket.org/petershinners/yter

    :param data: iterable
    :param ignore: types to ignore
    :return: bool
    """
    if ignore and isinstance(data, ignore):
        ret = False
    else:
        try:
            iter(data)
            ret = True
        except TypeError:
            ret = False

    return ret


def sorted_ignorecase(to_sort):
    """
    Sort a list of strings ignoring case.

    >>> L = ['foo', 'Foo', 'bar', 'Bar']
    >>> sorted(L)
    ['Bar', 'Foo', 'bar', 'foo']
    >>> sorted(L, key=lambda x: x.lower())
    ['bar', 'Bar', 'foo', 'Foo']
    >>>

    :param to_sort: iterable
    :returns: sorted data
    """
    return sorted(to_sort, key=lambda x: x.lower())


def is_true(value=None):
    """
    Returns a boolean value representing the "truth" of the value passed. The
    rules for what is a "True" value are:

        1. Integer/float values greater than 0
        2. The string values "True" and "true"
        3. Any object for which bool(obj) returns True

    :param value: some value
    :returns: bool
    """
    # First, try int/float conversion
    try:
        value = int(value)
    except (ValueError, TypeError):
        pass
    try:
        value = float(value)
    except (ValueError, TypeError):
        pass

    if isinstance(value, (six.integer_types, float)):
        ret = value > 0
    elif isinstance(value, six.string_types):
        ret = six.text_type(value).lower() == 'true'
    else:
        ret = bool(value)

    return ret


def simple_types_filter(data):
    """
    Convert the data list, dictionary into simple types, i.e., int, float, string,
    bool, etc.

    :param data: list or dict
    :returns: simple types: int, float, string
    """
    simpletypes_keys = (six.string_types, six.text_type, six.integer_types, float, bool)
    simpletypes_values = tuple(list(simpletypes_keys) + [list, tuple])

    if isinstance(data, (list, tuple)):
        simplearray = []
        for value in data:
            if value is not None:
                if isinstance(value, (dict, list)):
                    value = simple_types_filter(value)
                elif not isinstance(value, simpletypes_values):
                    value = repr(value)
            simplearray.append(value)
        data = simplearray

    elif isinstance(data, dict):
        simpledict = {}
        for key, value in six.iteritems(data):
            if key is not None and not isinstance(key, simpletypes_keys):
                key = repr(key)
            if value is not None and isinstance(value, (dict, list, tuple)):
                value = simple_types_filter(value)
            elif value is not None and not isinstance(value, simpletypes_values):
                value = repr(value)
            simpledict[key] = value
        data = simpledict

    return data


def stringify(data):
    """
    Given an iterable, returns its items as a list, with any non-string items
    converted to unicode strings.

    :param data: iterable data
    :returns: list of stringified data
    """
    ret = []
    for item in data:
        if six.PY2 and isinstance(item, str):
            item = stringutils.to_unicode(item)
        elif not isinstance(item, six.string_types):
            item = six.text_type(item)
        ret.append(item)
    return ret


def json_query(data, expr):
    """
    Query data using JMESPath language (http://jmespath.org).

    :param data: JSON query
    :param expr: expression
    :raises: RuntimeError
    :returns: search result
    """
    if jmespath is None:
        err = 'json_query requires jmespath module installed'
        log.error(err)
        raise RuntimeError(err)

    return jmespath.search(expr, data)
