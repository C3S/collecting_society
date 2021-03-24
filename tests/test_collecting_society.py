#!/usr/bin/env python
# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society

import unittest
import doctest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import test_view, test_depends
from trytond.tests.test_tryton import doctest_setup, doctest_teardown


class CollectingSocietyTestCase(unittest.TestCase):
    '''
    Test CollectingSociety module.
    '''

    def setUp(self):
        trytond.tests.test_tryton.install_module('collecting_society')

    def test0005views(self):
        '''
        Test views.
        '''
        test_view('collecting_society')

    def test0006depends(self):
        '''
        Test depends.
        '''
        test_depends()


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        CollectingSocietyTestCase))
    suite.addTests(doctest.DocFileSuite(
        'scenario_collecting_society.rst',
        setUp=doctest_setup, tearDown=doctest_teardown, encoding='utf-8',
        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS))
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
