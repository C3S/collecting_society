# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society

import uuid
from decimal import Decimal
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import PoolMeta
from collecting_society import MixinIdentifier

__all__ = [
    'Party',
    'PartyIdentifier',
    'PartyIdentifierName',
    'PartyCategory',
    'ContactMechanism',
    'Category',
    'Address'
]
__metaclass__ = PoolMeta


class Party:
    __name__ = 'party.party'
    _history = True

    web_user = fields.One2One(
        'web.user-party.party', 'party', 'user', 'Web User',
        help='The web user of the party')
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
    identifier_3rd_party = fields.Many2Many('party.identifier3rdparty',
            None, None, '3rd-party identifier', help='')

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


class PartyIdentifier(MixinIdentifier):
    __name__ = 'party.identifier'
    _history = True
    identifier = fields.Many2One('party.identifier.name', 'PartyIdentifierName', required=True, select=True, ondelete='CASCADE')
    party = fields.Many2One('party', 'Party', required=True, select=True, ondelete='CASCADE')


class PartyIdentifierName(ModelSQL, ModelView):
    __name__ = 'party.identifier.name'
    _history = True
    official_name = fields.Char('official name')
    version = fields.Char('version')


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
