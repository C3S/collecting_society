# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society

import pytest
from decimal import Decimal as D

import formulas
from tests.fixtures import (
    development_versions,
    base_values,
    relevance_values,
    adjustment_values,
    share_values,
)


# --- Fixtures ----------------------------------------------------------------

fixtures_total = [
    {
        'result': D('1234.56789'),
        'utilisation': {
            'base': D('1234.56789'),
            'relevance': D('1'),
            'share': D('1'),
            'adjustments': D('0'),
        },
    },
    {
        'result': D('1234567890.123456789012345679'),  # note: rounded
        'utilisation': {
            'base': D('1234567890.1234567890123456789'),
            'relevance': D('1'),
            'share': D('1'),
            'adjustments': D('0'),
        },
    },
    {
        'result': D('617.283945'),
        'utilisation': {
            'base': D('1234.56789'),
            'relevance': D('0.5'),
            'share': D('1'),
            'adjustments': D('0'),
        },
    },
    {
        'result': D('27.43333308369'),
        'utilisation': {
            'base': D('1234.56789'),
            'relevance': D('0.2'),
            'share': D('0.12345'),
            'adjustments': D('-0.1'),
        },
    },
]


# --- Tariff Total ------------------------------------------------------------

@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "base", base_values)
@pytest.mark.parametrize(
    "relevance", relevance_values)
@pytest.mark.parametrize(
    "share", share_values)
@pytest.mark.parametrize(
    "adjustments", adjustment_values)
def test_tariff_total(version, base, relevance, share, adjustments):
    version = formulas.convert_version(version)
    formula = getattr(formulas, f"tariff_total__{version}")
    assert formula(
        utilisation={
            'base': base,
            'relevance': relevance,
            'share': share,
            'adjustments': adjustments,
        }
    ) == base * relevance * share * (1 + adjustments)


@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "base", [
        D('-100'),
        D('-1'),
        D('-0.1'),
        D('-0.000001'),
    ])
def test_tariff_total_base_exception(version, base):
    version = formulas.convert_version(version)
    formula = getattr(formulas, f"tariff_total__{version}")
    with pytest.raises(AssertionError):
        formula(
            utilisation={
                'base': base,
                'relevance': D('1'),
                'share': D('1'),
                'adjustments': D('0'),
            }
        )


@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "relevance", [
        D('-100'),
        D('-1'),
        D('-0.1'),
        D('-0.000001'),
        D('0'),
        D('1.000001'),
        D('1.1'),
        D('2'),
        D('100'),
    ])
def test_tariff_total_relevance_exception(version, relevance):
    version = formulas.convert_version(version)
    formula = getattr(formulas, f"tariff_total__{version}")
    with pytest.raises(AssertionError):
        formula(
            utilisation={
                'base': D('1'),
                'relevance': relevance,
                'share': D('1'),
                'adjustments': D('0'),
            }
        )


@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "share", [
        D('-100'),
        D('-1'),
        D('-0.1'),
        D('-0.000001'),
        D('1.000001'),
        D('1.1'),
        D('2'),
        D('100'),
    ])
def test_tariff_total_share_exception(version, share):
    version = formulas.convert_version(version)
    formula = getattr(formulas, f"tariff_total__{version}")
    with pytest.raises(Exception):
        formula(
            utilisation={
                'base': D('1'),
                'relevance': D('1'),
                'share': share,
                'adjustments': D('0'),
            }
        )


@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "fixture", fixtures_total)
def test_tariff_total_fixtures(version, fixture):
    version = formulas.convert_version(version)
    formula = getattr(formulas, f"tariff_total__{version}")
    assert formula(
        utilisation=fixture['utilisation']
    ) == fixture['result']
