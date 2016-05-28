#################
   destructure
#################

Easy declarative schema validation with optional name-binding.

```
    from destructure import Binding, match

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
```


