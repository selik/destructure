#!/usr/bin/env python3
'''
Tests for Schema.
'''

import unittest
from destructure import *



class MatchAnyTestCase(unittest.TestCase):

    def test_any(self):
        schema = ...
        data = [1, 1.1, 1+1j, 'a', b'\x00']
        for datum in data:
            self.assertEqual(datum, match(schema, datum))



class MatchEqualTestCase(unittest.TestCase):

    def test_literal(self):
        data = [1, 1.1, 1+1j, 'a', b'\x00']
        for datum in data:
            self.assertEqual(datum, match(datum, datum))

        for datum in data:
            for other in set(data) - {datum}:
                with self.assertRaises(MatchError):
                    match(datum, other)



class MatchTypeTestCase(unittest.TestCase):

    def test_basic(self):
        data = [1, 1.1, 1+1j, 'a', b'\x00']
        types = [type(obj) for obj in data]
        for datum, typ in zip(data, types):
            self.assertEqual(datum, match(typ, datum))

        for datum in data:
            for other in set(types) - {type(datum)}:
                with self.assertRaises(MatchError):
                    match(datum, other)



class MatchCustomTypeTestCase(unittest.TestCase):

    def setUp(self):
        class Parent:
            def __init__(self, value):
                self.value = value
        self.Parent = Parent
        class Child(Parent):
            pass
        self.Child = Child

    def test_same(self):
        obj = self.Parent(1)
        self.assertEqual(obj, match(self.Parent, obj))

    def test_child(self):
        obj = self.Child(1)
        self.assertEqual(obj, match(self.Parent, obj))

    def test_wrong(self):
        with self.assertRaises(MatchError):
            match(self.Child, self.Parent(1))



class MatchSimpleMappingTestCase(unittest.TestCase):

    def setUp(self):
        self.schema = {'a': 1, 'b': int, 'c': ...}

    def test_correct(self):
        data = {'a': 1, 'b': 2, 'c': 3}
        self.assertEqual(data, match(self.schema, data))

    def test_missing(self):
        with self.assertRaises(MatchError):
            data = {'a': 1, 'b': 2}
            match(self.schema, data)

    def test_extra(self):
        with self.assertRaises(MatchError):
            data = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
            match(self.schema, data)



class MatchEllipsisMappingTestCase(unittest.TestCase):

    def test_extra_many(self):
        schema = {'a': 1, ...: ...}
        data = {'a': 1, 'b': 2, 'c': 3}
        self.assertEqual(data, match(schema, data))

    def test_extra_many_wrong(self):
        schema = {'a': 1, ...: ...}
        data = {}
        with self.assertRaises(MatchError):
            match(schema, data)

    def test_extra_one(self):
        schema = {'a': 1, 'b': 2, ...: int}
        data = {'a': 1, 'b': 2, 'c': 3}
        self.assertEqual(data, match(schema, data))

    def test_extra_one_missing(self):
        schema = {'a': 1, 'b': 2, ...: int}
        data = {'a': 1, 'b': 2}
        with self.assertRaises(MatchError):
            match(schema, data)



class MatchNestedMappingTestCase(unittest.TestCase):

    def test_two_layers(self):
        schema = {'a': 1,
                  'b': {'c': int, 'd': ...}}
        data = {'a': 1,
                  'b': {'c': 2, 'd': 3}}
        self.assertEqual(data, match(schema, data))

    def test_three_layers(self):
        schema = {'a': 1,
                  'b': {'c': int,
                        'd': {'a': 1, ...: ...}}}
        data = {'a': 1,
                  'b': {'c': 2,
                        'd': {'a': 1, 'b': 2}}}
        self.assertEqual(data, match(schema, data))



class MatchSimpleSequenceTestCase(unittest.TestCase):

    def test_correct(self):
        schema = [1, 2, int]
        data = [1, 2, 3]
        self.assertEqual(data, match(schema, data))

    def test_missing(self):
        schema = [1, 2, int]
        data = [1, 2]
        with self.assertRaises(MatchError):
            self.assertEqual(data, match(schema, data))

    def test_extra(self):
        schema = [1, 2, int]
        data = [1, 2]
        with self.assertRaises(MatchError):
            self.assertEqual(data, match(schema, data))



class MatchEllipsisSequenceTestCase(unittest.TestCase):

    def test_end(self):
        schema = [1, 2, ...]
        data = [1, 2, 3, 4]
        self.assertEqual(data, match(schema, data))

    def test_end_missing(self):
        schema = [1, 2, ...]
        data = [1]
        with self.assertRaises(MatchError):
            match(schema, data)

    def test_start(self):
        schema = [..., 3, 4]
        data = [1, 2, 3, 4]
        self.assertEqual(data, match(schema, data))

    def test_start_missing(self):
        schema = [..., 3, 4]
        data = [4]
        with self.assertRaises(MatchError):
            match(schema, data)

    def test_middle(self):
        schema = [1, ..., 4]
        data = [1, 2, 3, 4]
        self.assertEqual(data, match(schema, data))

    def test_middle_missing(self):
        schema = [1, 2, ..., 3, 4]
        data = [1, 4]
        with self.assertRaises(MatchError):
            match(schema, data)



class MatchNestedSequenceTestCase(unittest.TestCase):

    def test_two_layers(self):
        schema = [1, [2, int, ...]]
        data = [1, [2, 3, 4, 5, 6]]
        self.assertEqual(data, match(schema, data))

    def test_three_layers(self):
        schema = [1, [2, int, [...]]]
        data = [1, [2, 3, [4, 5, 6]]]
        self.assertEqual(data, match(schema, data))



class MatchInstanceTestCase(unittest.TestCase):

    def setUp(self):
        class Foo:
            def __init__(self, bar, **kwargs):
                self.bar = bar
                self.__dict__.update(**kwargs)
            def __eq__(self, other):
                return self.bar == other.bar

        self.Foo = Foo


    def test_equality(self):
        schema = self.Foo(bar=1)
        data = self.Foo(bar=1)

        result = match(schema, data)

        self.assertIsInstance(result, self.Foo)
        self.assertEqual(result.bar, 1)


    def test_inequality(self):
        schema = self.Foo(bar=1)
        data = self.Foo(bar=2)

        with self.assertRaises(MatchError):
            match(schema, data)


    def test_ignore_private(self):

        schema = self.Foo(bar=1, _baz=2)
        data = self.Foo(bar=1)

        self.assertTrue('_baz' in dir(schema))

        result = match(schema, data)

        self.assertIsInstance(result, self.Foo)
        self.assertEqual(result.bar, 1)


    def test_binding(self):
        o = Binding()
        schema = self.Foo(bar=o.x)
        data = self.Foo(bar=1)

        result = match(schema, data)

        self.assertIsInstance(result, self.Foo)
        self.assertEqual(result.bar, 1)

        self.assertEqual(o.x, 1)



class BindingTestCase(unittest.TestCase):

    def test_simple(self):
        o = Binding()
        schema = [1, 2, o.x]
        data = [1, 2, 3]
        self.assertEqual(data, match(schema, data))
        self.assertEqual(o.x, 3)

    def test_rebind(self):
        o = Binding()
        o.x = 1
        with self.assertRaises(BindError):
            o.x = 2

    def test_rebind_after_clear(self):
        o = Binding()
        o.x = 1
        self.assertEqual(1, o.x)
        del o.x
        o.x = 2
        self.assertEqual(2, o.x)

    def test_unwind(self):
        o = Binding()
        schema = [o.x, o.y, 42]
        data = [1, 2]
        with self.assertRaises(MatchError):
            match(schema, data)
        self.assertIsInstance(o.x, Unbound)
        self.assertIsInstance(o.y, Unbound)

    def test_two_in_same_schema(self):
        a = Binding()
        b = Binding()
        schema = [a.x, b.x]
        with self.assertRaises(SchemaError):
            match(schema, [1, 2])



class SwitchTestCase(unittest.TestCase):

    def test_guards(self):
        bind = Binding()
        schema = bind.x

        def one():
            return bind.x == 1
        def two():
            return bind.x == 2

        s = Switch(2)

        self.assertFalse(s.case(schema, one))
        self.assertIsInstance(bind.x, Unbound)

        self.assertTrue(s.case(schema, two))
        self.assertEqual(bind.x, 2)



if __name__ == '__main__':
    unittest.main()


