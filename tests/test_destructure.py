'''
Tests for Schema.
'''

import unittest
from schema import match, MatchError



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



class BindingTestCase(unittest.TestCase):

    def test_simple(self):
        o = Binding()
        schema = [1, 2, o.x]
        data = [1, 2, 3]
        self.assertEqual(match(schema, data))
        self.assertEqual(o.x, 3)



if __name__ == '__main__':
    unittest.main()

