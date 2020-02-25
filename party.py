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
    'PartyIdentifierSpace',
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
    identifiers = fields.One2Many(
        'party.identifier', 'party', '3rd-Party Identifier',
        help='The identifiers of the party')
    legal_person = fields.Boolean('Legal Person')
    common_public_interest = fields.Selection(
        [
            ('no', 'No'),
            ('on_approval', 'On Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ], 'Common Public Interest', required=True, sort=False)

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
    def default_common_public_interest():
        return 'no'

    @staticmethod
    def default_pocket_budget():
        return Decimal('0')


class PartyIdentifier(ModelSQL, ModelView, MixinIdentifier):
    'Party Identifier'
    __name__ = 'party.identifier'
    _history = True
    space = fields.Many2One(
        'party.identifier.space', 'Party Identifier Name',
        required=True, select=True, ondelete='CASCADE')
    party = fields.Many2One(
        'party.party', 'Party',
        required=True, select=True, ondelete='CASCADE')


class PartyIdentifierSpace(ModelSQL, ModelView):
    'Party Identifier Space'
    __name__ = 'party.identifier.space'
    _history = True
    name = fields.Char('Name of the ID space')
    version = fields.Char('Version')


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
