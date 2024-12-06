# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society

import pytest
from decimal import Decimal as D

import collection
from tests.fixtures import (
    development_versions,
    total_values,
)


# --- Fixtures ----------------------------------------------------------------

fixtures_fee = [
    {
        'result': D('0.1'),
        'total': D('1.0'),
    },
    {
        'result': D('123.456789'),
        'total': D('1234.56789'),
    },
]


# --- Tariff Fee --------------------------------------------------------------

@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "total", total_values)
def test_tariff_fee(version, total):
    version = collection.convert_version(version)
    formula = getattr(collection, f"tariff_fee__{version}")
    assert formula(total=total) == total * D('0.1')


@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "total", [
        D('-100'),
        D('-1'),
        D('-0.1'),
        D('-0.000001'),
    ])
def test_tariff_fee_total_exception(version, total):
    version = collection.convert_version(version)
    formula = getattr(collection, f"tariff_fee__{version}")
    with pytest.raises(AssertionError):
        formula(total=total)


@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "fixture", fixtures_fee)
def test_tariff_fee_fixtures(version, fixture):
    version = collection.convert_version(version)
    formula = getattr(collection, f"tariff_fee__{version}")
    assert formula(total=fixture['total']) == fixture['result']
