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

    def bind(self, unbound, value):
        setattr(unbound.namespace, unbound.name, value)
        # track name bindings to delete if match fails
        self.names.append(unbound)



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


