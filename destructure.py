#!/usr/bin/env python3
'''
Recursive schema verification for nested sequences and mappings.
Ideal for validating parsed JSON data structures.
'''

from collections.abc import Mapping, Sequence
from types import SimpleNamespace



__all__ = ['match',
           'Binding',
           'Switch',
           ]



class MatchError(ValueError):
    'Data did not match the specified schema'



class Unbound(AttributeError):
    'Attribute not bound to a value'

    def __init__(self, namespace, name):
        self.namespace = namespace
        self.name = name



class Binding(SimpleNamespace):
    '''
    A Binding object can be used to capture values from a schema matching.

        >>> o = Binding()
        >>> schema = [1, 2, o.x]
        >>> data = [1, 2, 3]
        >>> match(schema, data)
        [1, 2, 3]
        >>> o.x
        3
    '''

    def __getattr__(self, name):
        return Unbound(self, name)



class Switch:
    '''
    Try to match data to one or several schemas. The specified Binding
    will be cleared/unbound if a match fails.

        >>> o = Binding()
        >>> schema1 = [1, o.x]
        >>> schema2 = [2, o.x]
        >>> schema3 = [3, o.x]
        >>> s = Switch(data=[2, 2], binding=o)
        >>> if s.case(schema1):
        ...     print(o.x)
        ... elif s.case(schema2):
        ...     print(o.x)
        ... elif s.case(schema3):
        ...     print(o.x)
        ... else:
        ...     print('otherwise')
        2
    '''

    def __init__(self, *, data=None, binding=None):
        if binding is None:
            self.binding = Binding()
        else:
            self.binding = binding
        self.data = data


    def case(self, schema):
        '''
        Test a schema against the Switch's data.
        Clears the switch's Binding if the match fails.
        '''
        try:
            match(schema, self.data)
        except MatchError:
            self.binding.__dict__.clear()
            return False
        return True



def _match_type(schema, data):
    '''
    Verify that data is of the correct type.
    '''
    if not isinstance(data, schema):
        fmt = '{data!r} does not match type {schema.__name__!r}'
        raise MatchError(fmt.format(data=data, schema=schema))
    return data



def _match_mapping_ellipsis(schema, data):
    '''
    If ``schema[...] is ...`` then match all extra items.
    If ``schema[...] is not ...`` then match exactly 1 extra item.
    '''
    schema = schema.copy()
    value = schema.pop(...)

    extra = {k: v for k, v in data.items() if k not in schema}

    if value is ... or len(extra) == 1:
        schema.update(extra)
        return _match_mapping(schema, data)

    if not extra:
        fmt = '{{...: {value!r}}} specified, but no extra items found'
        raise MatchError(fmt.format(value=value))
    fmt = '\{...: {value!r}\} cannot match {n} extra items'
    raise MatchError(fmt.format(value=value, n=len(extra)))



def _match_mapping(schema, data):
    '''
    Recursively verify that data matches keys and values in the mapping.
    An ellipsis key-value pair specifies a variable number of items.
    '''
    if not isinstance(data, Mapping):
        fmt = 'expected a mapping, got {data.__class__.__name__!r}'
        raise MatchError(fmt.format(data=data))

    missing = schema.keys() - data.keys()
    excess = data.keys() - schema.keys()

    # Bug: data with Ellipsis as a key
    #      may prevent schema from using Ellipsis as desired.
    if missing == {...}:
        return _match_mapping_ellipsis(schema, data)

    if missing:
        fmt = 'missing {n} keys {keys!r}'
        raise MatchError(fmt.format(n=len(missing), keys=missing))

    if excess:
        fmt = 'got {n} unexpected keys {keys!r}'
        raise MatchError(fmt.format(n=len(excess), keys=excess))

    return {key: match(value, data[key]) for key, value in schema.items()}



def _match_sequence(schema, data):
    '''
    Recursively verify that data matches the sequence.
    An ellipsis specifies a variable number of items.
    '''
    if not isinstance(data, Sequence):
        fmt = 'expected a sequence, got {data.__class__.__name__!r}'
        raise MatchError(fmt.format(data=data))

    if data and not schema:
        fmt = 'expected empty {cls!r}, got {data!r}'
        raise MatchError(fmt.format(cls=type(schema).__name__, data=data))

    if ... not in schema:
        n = len(schema)
        m = len(data)
        if n > m:
            raise MatchError('got unexpected values {!r}'.format(data[n:]))
        if m < n:
            raise MatchError('missing values {!r}'.format(schema[m:]))
        cls = type(schema)
        return cls(map(match, schema, data))

    if ... is schema[-1]:
        split = len(schema) - 1
        return _match_sequence(schema[:-1], data[:split]) + data[split:]

    if ... is schema[0]:
        split = 1 - len(schema)
        return data[:split] + _match_sequence(schema[1:], data[split:])

    split = schema.index(...)
    return _match_sequence(schema[:split], data[:split]) \
           + _match_sequence(schema[split:], data[split:])



def _match_equal(schema, data):
    '''
    Verify that the data is exactly the schema.
    Intended to match non-collection literals.
    '''
    if schema != data:
        fmt = '{data!r} did not match literal {schema!r}'
        raise MatchError(fmt.format(data=data, schema=schema))
    return data



def match(schema, data):
    '''
    Verify data follows an expected structure. The structure may be
    specified as a schema of nested sequences, mappings, and types.
    Specifying a type in the schema will verify the data is an
    instance of that correct type. An ellipsis (...) may be used to
    specify a variable number of elements in a sequence or mapping. or
    may be used to specify that data may be of any type.

        >>> o = Binding()
        >>> schema = {
        ...     'string': str,
        ...     'any': ...,
        ...     'binding': o.name,
        ...     'sequence': [1, 2, ...],
        ...     'mapping': {'a': int, ...: ...}
        ... }
        >>> data = {
        ...     'string': 'a',
        ...     'any': 5j,
        ...     'binding': 42,
        ...     'sequence': [1, 2, 3, 4],
        ...     'mapping': {'a': 1, 'b': 2, 'c': 3}
        ... }
        >>> data == match(schema, data)
        True
        >>> o.name
        42
    '''
    if isinstance(schema, Unbound):
        obj = schema.namespace
        setattr(obj, schema.name, data)
        return data

    if schema is Ellipsis:
        return data

    if isinstance(schema, type):
        return _match_type(schema, data)

    if isinstance(schema, Mapping):
        return _match_mapping(schema, data)

    if isinstance(schema, Sequence) and not isinstance(schema, (str, bytes)):
        return _match_sequence(schema, data)

    return _match_equal(schema, data)


