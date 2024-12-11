# flake8: noqa: E501
#
# Usage:
#   cd formulas
#   PYTHONSTARTUP=tests/test_distribution.py python

import distribution
from decimal import Decimal
from fractions import Fraction
from pprint import pprint

roles = [{
    'plan': '0.0',
    'type': 'original',
    'creation': 'C00001',
    'meta': {
        'utilisation': 'U00001',
    },
    'split': {
        'lists': {
            'one': {'rightsholders': ['one']},
            'two': {'rightsholders': ['two1', 'two2']},
            'three': {'rightsholders': ['three1', 'three2', 'three3']},
            'deep': {
                'a': {'a-a': {'a-a-a': {'rightsholders': ['deep_even1']},
                              'a-a-b': {'rightsholders': ['deep_even2']}},
                      'a-b': {'a-b-a': {'rightsholders': []},
                              'a-b-b': {'rightsholders': []}}},
                'b': {'b-a': {'b-a-a': {'rightsholders': ['deep_filled1']},
                              'b-a-b': {'rightsholders': []}},
                      'b-b': {'b-b-a': {'rightsholders': ['deep_filled2']},
                              'b-b-b': {'rightsholders': []}}},
            },
            'missing': {
                'filled': {'rightsholders': ['missing']},
                'empty': {'rightsholders': []},
            },
            'empty': {
                'empty1': {'rightsholders': []},
                'empty2': {'rightsholders': []},
            },
        },
        'dicts': {
            'one': {'rightsholders': [{'licenser': 'one'}]},
            'two': {'rightsholders': [{'licenser': 'two'}]},
            'three': {'rightsholders': [{'licenser': 'three'}]},
            'fractions': {'rightsholders': [
                {'licenser': 'onesixth', 'fraction': Fraction(1, 6)},
                {'licenser': 'fivesixth', 'fraction': Fraction(5, 6)},
            ]},
        },
        'firstlevel': {
            'rightsholders': ['firstlevel'],
        },
        'firstlevelempty': {
            'rightsholders': [],
        },
        'newcover': [{
            'plan': '0.0',
            'type': 'cover',
            'creation': 'C00002',
            'meta': {
                'utilisation': 'U00001',
            },
            'split': {
                'coversplit1': {'rightsholders': ['cover1']},
                'coversplit2': {'rightsholders': ['cover2']},
            },
        }],
        'multiplecover': [
            {
                'plan': '0.0',
                'type': 'cover',
                'creation': 'C00004',
                'meta': {
                    'utilisation': 'U00001',
                },
                'split': {
                    'coversplit1': {'rightsholders': ['cover1']},
                    'coversplit2': {'rightsholders': []},
                },
            }, {
                'plan': '0.0',
                'type': 'cover',
                'creation': 'C00005',
                'meta': {
                    'utilisation': 'U00001',
                },
                'split': {
                    'coversplit1': {'rightsholders': ['cover1']},
                    'coversplit2': {'rightsholders': []},
                },
            },
        ],
    },
}]

fractions = {}


def generate_fractions(roles):
    # distribution
    if isinstance(roles, list):
        for distribution in roles:
            if distribution['type'] in fractions:
                continue
            fraction = generate_split(distribution['split'])
            if fraction:
                fractions[distribution['type']] = fraction
            generate_fractions(distribution['split'])
        return
    # rightsholders
    if 'rightsholders' in roles:
        return
    # split
    for key in roles:
        generate_fractions(roles[key])


def generate_split(roles, length=1):
    fractions = {}
    fractions['fraction'] = Fraction(1, length)
    # distribution
    if isinstance(roles, list):
        fractions['distribution'] = roles[0]['type']
        return fractions
    # rightsholders
    if 'rightsholders' in roles:
        return fractions
    # split
    fractions["split"] = {}
    for item in roles:
        split = generate_split(roles[item], len(roles))
        if split is not None:
            fractions["split"][item] = generate_split(roles[item], len(roles))
    return fractions

generate_fractions(roles)
distribution.fractions__0_0 = fractions
pprint(fractions)

split = distribution.Split(roles, Decimal('0.0001'), debug=True, verbose=False)
split.distribute(Decimal(1))
split.distribute(Decimal(10000))
