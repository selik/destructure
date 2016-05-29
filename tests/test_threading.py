'''
Testing for race conditions and deadlocks.
'''

from destructure import *
from destructure import Match
import random
from threading import Thread
import time
import unittest



class FuzzyBinding(Binding):
    'Delays getting an unbound attribute to reveal race conditions'

    def __setattr__(self, name, value):
        if not isinstance(getattr(self, name), Unbound):
            fmt = 'name {name!r} has already been bound to {value!r}'
            raise BindError(fmt.format(name=name, value=value))
        time.sleep(random.random())
        super(Binding, self).__setattr__(name, value)



class NoLockMatch(Match):

    def acquire_binding_lock(self):
        pass



class BindingDeadlockTestCase(unittest.TestCase):
    '''
    Test for two matches and two bindings causing deadlock.

    Multiple Binding objects in a single schema is not supported.

    To avoid deadlock in such a case, we'd need to traverse the schema
    looking for all Binding objects and acquire all their locks before
    doing any work. What a pain...

    '''

    def test_no_lock(self):
        errors = self.deadlock(NoLockMatch().match)
        self.assertEqual(2, sum(errors))

    @unittest.skip("Schemas may not have multiple Binding objects")
    def test_with_lock(self):
        blocked = self.deadlock(match)
        self.assertFalse(blocked)

    def deadlock(self, match):
        errors = []

        a = FuzzyBinding()
        b = FuzzyBinding()
        schema1 = [a.x, b.x]
        schema2 = [b.y, a.y]
        data = [1, 2]

        def worker(schema, data):
            try:
                match(schema, data)
            except SchemaError:
                errors.append(True)
            else:
                errors.append(False)

        t1 = Thread(target=worker, args=(schema1, data))
        t2 = Thread(target=worker, args=(schema2, data))

        def monitor():
            time.sleep(15)
            raise RuntimeError('deadlock suspected, please stop test')
        m = Thread(target=monitor)
        m.daemon = True
        m.start()

        threads = [t1, t2]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        return errors



class BindingRaceTestCase(unittest.TestCase):
    'test for two matches racing to bind a name'

    def test_no_lock(self):
        errors = self.race(NoLockMatch().match)
        self.assertEqual(0, sum(errors))

    def test_with_lock(self):
        errors = self.race(match)
        self.assertEqual(1, sum(errors))

    def race(self, match):
        errors = []

        o = FuzzyBinding()
        schema = o.x
        data = 1

        def worker():
            try:
                match(schema, data)
            except BindError:
                errors.append(True)
            else:
                errors.append(False)

        threads = [Thread(target=worker) for i in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        return errors



if __name__ == '__main__':
    unittest.main()


