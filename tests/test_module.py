# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society

from trytond.tests.test_tryton import ModuleTestCase


class CollectingSocietyTestCase(ModuleTestCase):
    'Test Collecting Society module'
    module = 'collecting_society'


del ModuleTestCase
