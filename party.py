# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society

import uuid
from decimal import Decimal
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = [
    'Party', 'PartyCategory', 'ContactMechanism', 'Category', 'Address'
]
__metaclass__ = PoolMeta


class Party:
    __name__ = 'party.party'
    _history = True

    member_c3s = fields.Boolean('Member of C3S')
    member_c3s_token = fields.Char('C3S Membership Token')
    artists = fields.One2Many('artist', 'party', 'Artists')
    default_solo_artist = fields.Many2One(
        'artist', 'Default Solo Artist',
        help='The default solo artist of this party')
    firstname = fields.Char('Firstname')
    lastname = fields.Char('Lastname')
    birthdate = fields.Date('Birth Date')
    repertoire_terms_accepted = fields.Boolean(
        'Terms of Service Acceptance for Repertoire')
    oid = fields.Char(
        'OID', required=True,
        help='A unique object identifier used in the public web api to avoid'
             'exposure of implementation details to the users.')

    @classmethod
    def __setup__(cls):
        super(Party, cls).__setup__()
        cls._sql_constraints += [
            ('uuid_oid', 'UNIQUE(oid)',
                'The OID of the client must be unique.'),
        ]

    @staticmethod
    def default_oid():
        return str(uuid.uuid4())

    @staticmethod
    def default_pocket_budget():
        return Decimal('0')


class PartyCategory():
    __name__ = 'party.party-party.category'
    _history = True


class ContactMechanism():
    __name__ = 'party.contact_mechanism'
    _history = True


class Category():
    __name__ = 'party.category'
    _history = True


class Address():
    __name__ = 'party.address'
    _history = True
