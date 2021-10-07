#!/usr/bin/env python
# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society

import unittest
import doctest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase
from trytond.tests.test_tryton import doctest_setup, doctest_teardown

from trytond.modules.party.tests import PartyCheckEraseMixin


class CollectingSocietyTestCase(PartyCheckEraseMixin, ModuleTestCase):
    'Test CollectingSociety module'
    module = 'collecting_society'

    def setUp(self):
        trytond.tests.test_tryton.activate_module('collecting_society')


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        CollectingSocietyTestCase))
    # suite.addTests(doctest.DocFileSuite(
    #     'scenario_collecting_society.rst',
    #     setUp=doctest_setup, tearDown=doctest_teardown, encoding='utf-8',
    #     optionflags=doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS))
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
