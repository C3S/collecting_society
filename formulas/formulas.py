# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society

from datetime import datetime
from decimal import Decimal, getcontext
from functools import reduce
from math import ceil
from operator import add
from typing import TypedDict, NotRequired

getcontext().prec = 28


def convert_version(version):
    return version.replace(".", "_")


# === Types ===================================================================

class Utilisation(TypedDict):
    base: Decimal
    relevance: Decimal
    share: Decimal
    adjustments: Decimal


class Adjustments(TypedDict):
    electronic_submission: NotRequired[Decimal]
    small: NotRequired[Decimal]
    benefit: NotRequired[Decimal]
    social_cultural_religious: NotRequired[Decimal]
    promotion_of_young_artists: NotRequired[Decimal]
    missing_playlist_fee: NotRequired[Decimal]


class Event(TypedDict):
    start: NotRequired[datetime]
    end: NotRequired[datetime]
    attendants: int
    max_attendants: int
    max_admission: Decimal
    turnover_tickets: Decimal
    turnover_benefit: Decimal
    expenses_musicians: Decimal
    expenses_production: Decimal


# === Tariffs =================================================================

# --- Tariff Total ------------------------------------------------------------

def tariff_total__0_1(utilisation: Utilisation):
    # sanity checks
    assert utilisation['base'] > 0
    assert 0 < utilisation['relevance'] <= 1
    assert 0 <= utilisation['share'] <= 1
    # total
    return (
        utilisation['base']
        * utilisation['relevance']
        * utilisation['share']
        * (1 - utilisation['adjustments'])
    )


def tariff_total__0_2(utilisation: Utilisation):
    return tariff_total__0_1(utilisation)


def tariff_total__0_3(utilisation: Utilisation):
    return tariff_total__0_1(utilisation)


# --- Tariff Fee --------------------------------------------------------------

def tariff_fee__0_1(total: Decimal):
    # sanity checks
    assert 0 <= total, f"invalid range of tariff total: {total}"
    # fee
    return total * Decimal('0.1')


def tariff_fee__0_2(total: Decimal):
    return tariff_fee__0_1(total)


def tariff_fee__0_3(total: Decimal):
    return tariff_fee__0_1(total)


# --- Tariff Live -------------------------------------------------------------

# --- Tariff Live Base

def tariff_base__L0_1(context: Event, represented_ratio: Decimal):
    # sanity checks
    assert 0 <= represented_ratio <= 1, \
           f"invalid range of tariff represented_ratio: {represented_ratio}"
    # base
    base_turnover = context['turnover_tickets'] + context['turnover_benefit']
    base_expenses = \
        context['expenses_musicians'] + context['expenses_production']
    base_minimum = ceil(context['attendants'] / 10) * 10 * Decimal('0.83')
    base_total = max(base_minimum, base_turnover or base_expenses)
    return base_total * represented_ratio


def tariff_base__L0_2(context: Event, represented_ratio: Decimal):
    return tariff_base__L0_1(context, represented_ratio)


def tariff_base__L0_3(context: Event, represented_ratio: Decimal):
    return tariff_base__L0_1(context, represented_ratio)


# --- Tariff Live Relevance

def tariff_relevance__L0_1(context: Event, relevance: Decimal):
    # sanity checks
    assert 0 < relevance <= 1, \
           f"invalid range of relevance: {relevance}"
    # relevance
    return relevance


def tariff_relevance__L0_2(context: Event, relevance: Adjustments):
    return tariff_relevance__L0_1(context, relevance)


def tariff_relevance__L0_3(context: Event, relevance: Adjustments):
    return tariff_relevance__L0_1(context, relevance)


# --- Tariff Live Share

def tariff_share__L0_1(context: Event):
    return Decimal('0.1')


def tariff_share__L0_2(context: Event):
    return tariff_share__L0_1(context)


def tariff_share__L0_3(context: Event):
    return tariff_share__L0_1(context)


# --- Tariff Live Adjustments

def tariff_adjustments__L0_1(context: Event, adjustments: Adjustments):
    return reduce(add, [
        adjustments.get('electronic_submission', 0),
        adjustments.get('small', 0),
        adjustments.get('benefit', 0),
        adjustments.get('social_cultural_religious', 0),
        adjustments.get('promotion_of_young_artists', 0),
        adjustments.get('missing_playlist_fee', 0),
    ])


def tariff_adjustments__L0_2(context: Event, adjustments: Adjustments):
    return tariff_adjustments__L0_1(context, adjustments)


def tariff_adjustments__L0_3(context: Event, adjustments: Adjustments):
    return tariff_adjustments__L0_1(context, adjustments)
