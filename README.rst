#################
   destructure
#################

Easy declarative schema validation with optional name-binding.

.. code:: python

    >>> from destructure import Binding, match
    >>>
    >>> o = Binding()
    >>> schema = {
    ...     'string': str,
    ...     'any': ...,
    ...     'binding': o.name,
    ...     'sequence': [1, 2, ...],
    ...     'mapping': {'a': int, ...: ...},
    ... }
    >>> data = {
    ...     'string': 'a',
    ...     'any': 5j,
    ...     'binding': 42,
    ...     'sequence': [1, 2, 3, 4],
    ...     'mapping': {'a': 1, 'b': 2, 'c': 3},
    ... }
    >>> data == match(schema, data)
    True
    >>> o.name
    42


Pick between several schemas with a handy ``Switch.case``.

.. code:: python

    >>> from destructure import Binding, Switch
    >>>
    >>> o = Binding()
    >>> schema1 = [1, o.x]
    >>> schema2 = [2, o.x]
    >>>
    >>> s = Switch([2, 2])
    >>> if s.case(schema1):
    ...     print(o.x)
    ... elif s.case(schema2):
    ...     print(o.x)
    ... else:
    ...     print('otherwise')
    2


Schemas may validate and unpack custom class attributes. This feature
is restricted to classes that can be constructed with keyword
arguments. Binding objects may be used so long as the class does not
have aggressive argument type-checking.

.. code:: python

    >>> class Foo:
    ...     def __init__(self, bar):
    ...         self.bar = bar
    >>> bind = Binding()
    >>> schema = Foo(bar=bind.x)
    >>> result = match(schema, Foo(bar=1))
    >>> bind.x
    1
