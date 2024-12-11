# flake8: noqa: E501
#
# Usage:
#   cd formulas
#   PYTHONSTARTUP=tests/_test_distribution_docstring.py python

import distribution
from decimal import Decimal
from fractions import Fraction
from pprint import pprint

distribution.fractions__0_0_1 = {
    'original': {
        'fraction': 1,
        'split': {
            'copyright': {
                'fraction': Fraction(1, 2),
            },
            'ancillary': {
                'fraction': Fraction(1, 2),
            },
        },
    },
}

roles = [{
   'plan': '0.0.1',
   'type': 'original',
   'creation': 'C00001',
   'meta': {'utilisation': 'U00001'},
   'split': {
       'copyright': {
           'rightsholders': [
               {'licenser': 'licenser1', 'fraction': Fraction(2, 3)},
               {'licenser': 'licenser2', 'fraction': Fraction(1, 3)},
            ],
       },
       'ancillary': {
           'rightsholders': [],
       },
   },
}]

split = distribution.Split(roles)
shares = split.distribute(Decimal(1000))
pprint(shares)
