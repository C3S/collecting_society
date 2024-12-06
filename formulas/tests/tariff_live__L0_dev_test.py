# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society

import pytest
from math import ceil
from decimal import Decimal as D
from itertools import combinations

import collection
from tests.fixtures import (
    development_versions,
    money_values,
    billable_ratio_values,
    attendant_values,
    relevance_values,
    adjustment_categories,
    adjustment_position_values,
)


# --- Fixtures ----------------------------------------------------------------

development_fixtures_tariff_live_base = [
    {
        'result': D('200'),
        'billable_ratio': D('1'),
        'context': {
            'attendants': D('100'),
            'turnover_tickets': D('100'),
            'turnover_benefit': D('100'),
            'expenses_musicians': D('0'),
            'expenses_production': D('0'),
        },
    },
    {
        'result': D('3535.835148'),
        'billable_ratio': D('0.9876'),
        'context': {
            'attendants': D('1234'),
            'turnover_tickets': D('1234.56'),
            'turnover_benefit': D('2345.67'),
            'expenses_musicians': D('0'),
            'expenses_production': D('0'),
        },
    },
    {
        'result': D('3535.835148'),
        'billable_ratio': D('0.9876'),
        'context': {
            'attendants': D('1234'),
            'turnover_tickets': D('0'),
            'turnover_benefit': D('0'),
            'expenses_musicians': D('1234.56'),
            'expenses_production': D('2345.67'),
        },
    },
    {
        'result': D('127.003280'),
        'billable_ratio': D('0.1234'),
        'context': {
            'attendants': D('1234'),
            'turnover_tickets': D('1'),
            'turnover_benefit': D('1'),
            'expenses_musicians': D('0'),
            'expenses_production': D('0'),
        },
    },
]

development_fixtures_tariff_live_relevance = [
    {
        'result': D('1'),
        'relevance': D('1'),
        'context': {
            'attendants': D('100'),
            'turnover_tickets': D('100'),
            'turnover_benefit': D('100'),
            'expenses_musicians': D('0'),
            'expenses_production': D('0'),
        },
    },
    {
        'result': D('0.5'),
        'relevance': D('0.5'),
        'context': {
            'attendants': D('1000'),
            'turnover_tickets': D('0'),
            'turnover_benefit': D('0'),
            'expenses_musicians': D('100'),
            'expenses_production': D('100'),
        },
    },
    {
        'result': D('0.1'),
        'relevance': D('0.1'),
        'context': {
            'attendants': D('10'),
            'turnover_tickets': D('100'),
            'turnover_benefit': D('100'),
            'expenses_musicians': D('0'),
            'expenses_production': D('0'),
        },
    },
]

development_fixtures_tariff_live_adjustments = [
    {
        'result': D('0'),
        'context': {
            'attendants': D('100'),
            'turnover_tickets': D('100'),
            'turnover_benefit': D('100'),
            'expenses_musicians': D('0'),
            'expenses_production': D('0'),
        },
        'adjustments': {
            'electronic_submission': D('0'),
            'small': D('0'),
            'benefit': D('0'),
            'social_cultural_religious': D('0'),
            'promotion_of_young_artists': D('0'),
            'missing_playlist_fee': D('0'),
        },
    },
    {
        'result': D('6'),
        'context': {
            'attendants': D('100'),
            'turnover_tickets': D('100'),
            'turnover_benefit': D('100'),
            'expenses_musicians': D('0'),
            'expenses_production': D('0'),
        },
        'adjustments': {
            'electronic_submission': D('1'),
            'small': D('1'),
            'benefit': D('1'),
            'social_cultural_religious': D('1'),
            'promotion_of_young_artists': D('1'),
            'missing_playlist_fee': D('1'),
        },
    },
    {
        'result': D('-6'),
        'context': {
            'attendants': D('100'),
            'turnover_tickets': D('100'),
            'turnover_benefit': D('100'),
            'expenses_musicians': D('0'),
            'expenses_production': D('0'),
        },
        'adjustments': {
            'electronic_submission': D('-1'),
            'small': D('-1'),
            'benefit': D('-1'),
            'social_cultural_religious': D('-1'),
            'promotion_of_young_artists': D('-1'),
            'missing_playlist_fee': D('-1'),
        },
    },
    {
        'result': D('0'),
        'context': {
            'attendants': D('100'),
            'turnover_tickets': D('100'),
            'turnover_benefit': D('100'),
            'expenses_musicians': D('0'),
            'expenses_production': D('0'),
        },
        'adjustments': {
            'electronic_submission': D('0.1'),
            'missing_playlist_fee': D('-0.1'),
        },
    },
    {
        'result': D('0.1'),
        'context': {
            'attendants': D('100'),
            'turnover_tickets': D('100'),
            'turnover_benefit': D('100'),
            'expenses_musicians': D('0'),
            'expenses_production': D('0'),
        },
        'adjustments': {
            'electronic_submission': D('0.1'),
        },
    },
]

development_fixtures_tariff_live = [
    {
        'result': D('141.433405920'),
        'billable_ratio': D('0.9876'),
        'context': {
            'attendants': D('100'),
            'turnover_tickets': D('1234.56'),
            'turnover_benefit': D('2345.67'),
            'expenses_musicians': D('0'),
            'expenses_production': D('0'),
        },
        'relevance': D('0.5'),
        'share': D('0.1'),
        'adjustments': {
            'electronic_submission': D('-0.1'),
            'small': D('0'),
            'benefit': D('0'),
            'social_cultural_religious': D('0'),
            'promotion_of_young_artists': D('-0.1'),
            'missing_playlist_fee': D('0'),
        },
    },
]


# --- Tariff Live -------------------------------------------------------------

# --- Tariff Live Base

@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "turnover_tickets, turnover_benefit", money_values)
@pytest.mark.parametrize(
    "billable_ratio", billable_ratio_values)
def test_tariff_live_base_turnover(
        version, turnover_tickets, turnover_benefit, billable_ratio):
    version = collection.convert_version(version)
    formula = getattr(collection, f"tariff_base__L{version}")
    assert formula(
        context={
            'attendants': 1,
            'turnover_tickets': turnover_tickets,
            'turnover_benefit': turnover_benefit,
            'expenses_musicians': D('0'),
            'expenses_production': D('0'),
        },
        billable_ratio=billable_ratio
    ) == (turnover_tickets + turnover_benefit) * billable_ratio
    assert formula(
        context={
            'attendants': 1,
            'turnover_tickets': turnover_tickets,
            'turnover_benefit': turnover_benefit,
            'expenses_musicians': D('1'),
            'expenses_production': D('1'),
        },
        billable_ratio=billable_ratio
    ) == (turnover_tickets + turnover_benefit) * billable_ratio


@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "expenses_musicians,expenses_production", money_values)
@pytest.mark.parametrize(
    "billable_ratio", billable_ratio_values)
def test_tariff_live_base_expenses(
        version, expenses_musicians, expenses_production, billable_ratio):
    version = collection.convert_version(version)
    formula = getattr(collection, f"tariff_base__L{version}")
    assert formula(
        context={
            'attendants': 1,
            'turnover_tickets': D('0'),
            'turnover_benefit': D('0'),
            'expenses_musicians': expenses_musicians,
            'expenses_production': expenses_production,
        },
        billable_ratio=billable_ratio
    ) == (expenses_musicians + expenses_production) * billable_ratio


@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "attendants", attendant_values)
@pytest.mark.parametrize(
    "billable_ratio", billable_ratio_values)
def test_tariff_live_base_minimum(version, attendants, billable_ratio):
    version = collection.convert_version(version)
    formula = getattr(collection, f"tariff_base__L{version}")
    minimum = ceil(attendants / 10) * 10 * D('0.83')
    assert formula(
        context={
            'attendants': attendants,
            'turnover_tickets': D('0'),
            'turnover_benefit': D('0'),
            'expenses_musicians': D('1'),
            'expenses_production': D('1'),
        },
        billable_ratio=billable_ratio
    ) == minimum * billable_ratio
    assert formula(
        context={
            'attendants': attendants,
            'turnover_tickets': D('1'),
            'turnover_benefit': D('1'),
            'expenses_musicians': D('0'),
            'expenses_production': D('0'),
        },
        billable_ratio=billable_ratio
    ) == minimum * billable_ratio


@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "billable_ratio", [
        D('-100'),
        D('-2'),
        D('-1'),
        D('-0.000001'),
        D('1.000001'),
        D('2'),
        D('100'),
    ])
def test_tariff_live_base_billable_ratio_exception(
        version, billable_ratio):
    version = collection.convert_version(version)
    formula = getattr(collection, f"tariff_base__L{version}")
    with pytest.raises(AssertionError):
        formula(
            context={
                'attendants': 0,
                'turnover_tickets': D('100'),
                'turnover_benefit': D('100'),
                'expenses_musicians': D('0'),
                'expenses_production': D('0'),
            },
            billable_ratio=billable_ratio
        )


@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "fixture", development_fixtures_tariff_live_base)
def test_tariff_live_base_fixtures(version, fixture):
    version = collection.convert_version(version)
    formula = getattr(collection, f"tariff_base__L{version}")
    assert formula(
        context=fixture['context'],
        billable_ratio=fixture['billable_ratio']
    ) == fixture['result']


# --- Tariff Live Relevance

@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "relevance", relevance_values)
def test_tariff_live_relevance(version, relevance):
    version = collection.convert_version(version)
    formula = getattr(collection, f"tariff_relevance__L{version}")
    assert formula(
        context={},
        relevance=relevance
    ) == relevance


@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "relevance", [
        D('-100'),
        D('-2'),
        D('-1'),
        D('-0.000001'),
        D('0'),
        D('1.000001'),
        D('2'),
        D('100'),
    ])
def test_tariff_live_relevance_exception(version, relevance):
    version = collection.convert_version(version)
    formula = getattr(collection, f"tariff_relevance__L{version}")
    with pytest.raises(AssertionError):
        assert formula(
            context={},
            relevance=relevance
        )


@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "fixture", development_fixtures_tariff_live_relevance)
def test_tariff_live_relevance_fixtures(version, fixture):
    version = collection.convert_version(version)
    formula = getattr(collection, f"tariff_relevance__L{version}")
    assert formula(
        context=fixture['context'],
        relevance=fixture['relevance']
    ) == fixture['result']


# --- Tariff Live Share

@pytest.mark.parametrize(
    "version", development_versions)
def test_tariff_live_share(version):
    version = collection.convert_version(version)
    formula = getattr(collection, f"tariff_share__L{version}")
    assert formula(
        context={},
    ) == D('0.1')


# --- Tariff Live Adjustments

@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "category", adjustment_categories)
@pytest.mark.parametrize(
    "value", adjustment_position_values)
def test_tariff_live_adjustments_single(version, category, value):
    version = collection.convert_version(version)
    formula = getattr(collection, f"tariff_adjustments__L{version}")
    assert formula(
        context={},
        adjustments={
            category: value
        }
    ) == value


@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "cat1, cat2", combinations(adjustment_categories, 2))
@pytest.mark.parametrize(
    "value", adjustment_position_values)
def test_tariff_live_adjustments_pairs(version, cat1, cat2, value):
    version = collection.convert_version(version)
    formula = getattr(collection, f"tariff_adjustments__L{version}")
    assert formula(
        context={},
        adjustments={
            cat1: value,
            cat2: value,
        }
    ) == value * 2


@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "value", adjustment_position_values)
def test_tariff_live_adjustments_all(version, value):
    version = collection.convert_version(version)
    formula = getattr(collection, f"tariff_adjustments__L{version}")
    assert formula(
        context={},
        adjustments={
            category: value for category in adjustment_categories
        }
    ) == value * len(adjustment_categories)


@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "fixture", development_fixtures_tariff_live_adjustments)
def test_tariff_live_adjustment_fixtures(version, fixture):
    version = collection.convert_version(version)
    formula = getattr(collection, f"tariff_adjustments__L{version}")
    assert formula(
        context=fixture['context'],
        adjustments=fixture['adjustments']
    ) == fixture['result']


# --- Tariff Live Fixtures

@pytest.mark.parametrize(
    "version", development_versions)
@pytest.mark.parametrize(
    "fixture", development_fixtures_tariff_live)
def test_tariff_live_fixtures(version, fixture):
    version = collection.convert_version(version)
    formula_base = getattr(collection, f"tariff_base__L{version}")
    formula_relevance = getattr(collection, f"tariff_relevance__L{version}")
    formula_adjustments = getattr(collection,
                                  f"tariff_adjustments__L{version}")
    formula_total = getattr(collection, f"tariff_total__{version}")
    assert formula_total(
        utilisation={
            'base': formula_base(
                context=fixture['context'],
                billable_ratio=fixture['billable_ratio']
            ),
            'relevance': formula_relevance(
                context=fixture['context'],
                relevance=fixture['relevance']
            ),
            'share': fixture['share'],
            'adjustments': formula_adjustments(
                context=fixture['context'],
                adjustments=fixture['adjustments']
            ),
        }
    ) == fixture['result']
