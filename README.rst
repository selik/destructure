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
    >>> guard = lambda : o.name > 10
    >>> data == match(schema, data, guard)
    True
    >>> o.name
    42


Pick between several schemas with a handy ``Switch.case``.

.. code:: python

    >>> from destructure import Binding, Switch
    >>>
    >>> o = Binding()
    >>> schema1 = [1, o.x, 3]
    >>> schema2 = [2, 4, o.x]
    >>>
    >>> s = Switch([2, 4, 6])
    >>> if s.case(schema1):
    ...     print(o.x)
    ... elif s.case(schema2):
    ...     print(o.x)
    ... else:
    ...     print('otherwise')
    6

Schemas may include many kinds of objects, though to make use of
Ellipses or Binding, the class must support keyword arguments and
cannot be too strict with parameter type-checking.

.. code:: python

    >>> class Foo:
    ...     def __init__(self, bar):
    ...         self.bar = bar
    >>> bind = Binding()
    >>> schema = Foo(bar=bind.x)
    >>> result = match(schema, Foo(bar=1))
    >>> bind.x
    1


See some `example scripts`_ for a practical usage, in context.

.. _`example scripts`: http://github.com/selik/destructure/tree/master/examples
