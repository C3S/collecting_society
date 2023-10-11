# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society

import pytest
from trytond.tests.test_tryton import doctest_setup


@pytest.fixture(autouse=True)
def doctest(request):
    if request.path.match("*.rst"):
        doctest_setup(None)
