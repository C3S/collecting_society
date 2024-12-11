# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society

import collection
from decimal import Decimal as D


# --- Fixtures ----------------------------------------------------------------

development_versions = [
    '0.1',
    # '0.2',
    # '0.3',
]

base_values = [
    D('0'),
    D('10'),
    D('100'),
    D('1000'),
]
relevance_values = [
    D('0.1'),
    D('0.5'),
    D('1'),
]
share_values = [
    D('0'),
    D('0.25'),
    D('0.5'),
    D('0.75'),
    D('1'),
]
relevance_values = [
    D('0.01'),
    D('0.25'),
    D('0.5'),
    D('0.75'),
    D('1'),
]
adjustment_values = [
    D('-2.0'),
    D('-1.0'),
    D('-0.5'),
    D('0.5'),
    D('1.0'),
    D('2.0'),
]
total_values = [
    D('0.0'),
    D('1.0'),
    D('10.0'),
    D('100.0'),
    D('1000.0'),
    D('10000.0'),
]

adjustment_categories = collection.Adjustments.__annotations__.keys()
adjustment_position_values = [
    D('-2.0'),
    D('-1.0'),
    D('-0.5'),
    D('0.0'),
    D('0.5'),
    D('1.0'),
    D('2.0'),
]
money_values = [
    (D('10'), D('10')),
    (D('100'), D('100')),
    (D('1000'), D('1000')),
    (D('10000'), D('10000')),
]
billable_ratio_values = [
    D('0'),
    D('0.25'),
    D('0.5'),
    D('0.75'),
    D('1'),
]
attendant_values = [
    10,
    100,
    1000,
    10000,
]
