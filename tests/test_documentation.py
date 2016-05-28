'''
Verify all docstring examples are working.
'''

import doctest



def test(module):
    doctest.testmod(module)
    print('.', end='')



print('Doctests:', end=' ')

import destructure; test(destructure)

print()
