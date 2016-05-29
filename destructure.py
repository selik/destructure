#!/usr/bin/env python3
'''
Recursive schema verification for nested sequences and mappings.
Ideal for validating parsed JSON data structures.
'''

from collections.abc import Mapping, Sequence
from threading import Lock
from types import SimpleNamespace



__all__ = ['match',
           'Binding',
           'Switch',
           'Unbound',
           'MatchError',
           'BindError',
           ]



class MatchError(ValueError):
    'Data did not match the specified schema'



class BindError(ValueError):
    'Could not bind value to name'



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

    __slots__ = ('_lock')

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)
        self._lock = Lock()


    def __getattr__(self, name):
        return Unbound(self, name)

    def __setattr__(self, name, value):
        if not isinstance(getattr(self, name), Unbound):
            fmt = 'name {name!r} has already been bound to {value!r}'
            raise BindError(fmt.format(name=name, value=value))
        super().__setattr__(name, value)


    def __enter__(self):
        self._lock.acquire()

    def __exit__(self):
        self._lock.release()



class Switch:
    '''
    Try to match data to one or several schemas.

        >>> o = Binding()
        >>> schema1 = [1, o.x]
        >>> schema2 = [2, o.x]
        >>> s = Switch([2, 2])
        >>> if s.case(schema1):
        ...     print(o.x)
        ... elif s.case(schema2):
        ...     print(o.x)
        ... else:
        ...     print('otherwise')
        2
    '''

    def __init__(self, data):
        self.data = data


    def case(self, schema):
        '''
        Test a schema against the Switch's data.
        '''
        try:
            match(schema, self.data)
        except MatchError:
            return False
        return True



class Match:
    '''
    Validator. Makes name-bindings during schema validation.
    Use as context manager to delete the name-bindings if match fails.

        with Match() as session:
            return session._match(schema, data)

    The ``Match`` interface is not guaranteed stable.
    Please use the function ``match`` instead.
    '''

    def __init__(self):
        self.names = []
        self.namespaces = []

    def __enter__(self):
        return self

    def __exit__(self, etype, e, traceback):
        if etype is MatchError:
            for unbound in self.names:
                delattr(unbound.namespace, unbound.name)
        for binding in self.namespaces:
            binding._lock.release()



    def match_type(self, schema, data):
        '''
        Verify that data is of the correct type.
        '''
        if not isinstance(data, schema):
            fmt = '{data!r} does not match type {schema.__name__!r}'
            raise MatchError(fmt.format(data=data, schema=schema))
        return data



    def match_mapping_ellipsis(self, schema, data):
        '''
        If ``schema[...] is ...`` then match all extra items.
        If ``schema[...] is not ...`` then match exactly 1 extra item.
        '''
        schema = schema.copy()
        value = schema.pop(...)

        extra = {k: v for k, v in data.items() if k not in schema}

        if value is ... or len(extra) == 1:
            schema.update(extra)
            return self.match_mapping(schema, data)

        if not extra:
            fmt = '{{...: {value!r}}} specified, but no extra items found'
            raise MatchError(fmt.format(value=value))
        fmt = '\{...: {value!r}\} cannot match {n} extra items'
        raise MatchError(fmt.format(value=value, n=len(extra)))



    def match_mapping(self, schema, data):
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
            return self.match_mapping_ellipsis(schema, data)

        if missing:
            fmt = 'missing {n} keys {keys!r}'
            raise MatchError(fmt.format(n=len(missing), keys=missing))

        if excess:
            fmt = 'got {n} unexpected keys {keys!r}'
            raise MatchError(fmt.format(n=len(excess), keys=excess))

        return {k: self.match(nest, data[k]) for k, nest in schema.items()}



    def match_sequence(self, schema, data):
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
                fmt = 'got unexpected values {!r}'
                raise MatchError(fmt.format(data[n:]))
            if m < n:
                fmt = 'missing values {!r}'
                raise MatchError(fmt.format(schema[m:]))
            cls = type(schema)
            return cls(map(self.match, schema, data))

        if ... is schema[-1]:
            split = len(schema) - 1
            matched = self.match_sequence(schema[:-1], data[:split])
            return matched + data[split:]

        if ... is schema[0]:
            split = 1 - len(schema)
            matched = self.match_sequence(schema[1:], data[split:])
            return data[:split] + matched

        split = schema.index(...)
        return self.match_sequence(schema[:split], data[:split]) \
               + self.match_sequence(schema[split:], data[split:])



    def match_equal(self, schema, data):
        '''
        Verify that the data is exactly the schema.
        Intended to match non-collection literals.
        '''
        if schema != data:
            fmt = '{data!r} did not match literal {schema!r}'
            raise MatchError(fmt.format(data=data, schema=schema))
        return data



    def bind(self, unbound, value):
        '''
        Bind value to Binding attribute.
        '''

        # lock Binding for thread-safety
        # track Binding to unlock after match is complete
        if unbound.namespace not in self.namespaces:
            unbound.namespace._lock.acquire()
            self.namespaces.append(unbound.namespace)

        setattr(unbound.namespace, unbound.name, value)

        # track name bindings to delete if match fails
        self.names.append(unbound)



    def match(self, schema, data):
        '''
        Recursive schema validation and name-binding.
        '''
        if isinstance(schema, Unbound):
            self.bind(schema, data)
            return data

        if schema is Ellipsis:
            return data

        if isinstance(schema, type):
            return self.match_type(schema, data)

        if isinstance(schema, Mapping):
            return self.match_mapping(schema, data)

        if isinstance(schema, Sequence) and not isinstance(schema, (str, bytes)):
            return self.match_sequence(schema, data)

        return self.match_equal(schema, data)



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

    A failed match will unwind any bindings made during the attempt.
    '''

    with Match() as session:
        return session.match(schema, data)



if __name__ == '__main__':
    pass


