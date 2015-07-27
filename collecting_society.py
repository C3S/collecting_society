# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society
import uuid
import datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from collections import Counter, defaultdict
from sql.functions import CharLength

from trytond.model import ModelView, ModelSQL, fields
from trytond.wizard import Wizard, StateView, Button, StateTransition

from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.pyson import Eval, Bool, Or


__all__ = [
    'Client',
    'Artist',
    'ArtistArtist',
    'ArtistPayeeAcceptance',
    'Identifier',
    'Identification',
    'Creation',
    'CreationOriginalDerivative',
    'CreationContribution',
    'CreationRole',
    'ContributionRole',
    'License',
    'CreationLicense',
    'Distribution',
    'Allocation',
    'Utilisation',
    'Utilisation',
    'UtilisationIMP',
    'UtilisationIMPIdentifyStart',
    'UtilisationIMPIdentify',
    'DistributeStart',
    'Distribute',
    'STATES',
    'DEPENDS',
]
STATES = {
    'readonly': ~Eval('active'),
}
DEPENDS = ['active']
SEPARATOR = u' /25B6 '


class Client(ModelSQL, ModelView):
    'Client'
    __name__ = 'client'
    _rec_name = 'uuid'
    web_user = fields.Many2One('web.user', 'Web User', required=True)
    uuid = fields.Char(
        'UUID', required=True, help='The universally unique identifier '
        'of the client used by a web user')
    player_name = fields.Char(
        'Player Name', required=True,
        help='Name of the media player used by the client')
    player_version = fields.Char(
        'Player Version',
        help='Version of the client media player used by the client')
    plugin_name = fields.Char(
        'Plugin Name', help='Name of the plugin used by the media player')
    plugin_version = fields.Char(
        'Plugin Version', help='The version of the plugin used '
        'by the media player')
    plugin_vendor = fields.Char(
        'Plugin Vendor', help='Vendor of the plugin used by the media player')
    active = fields.Boolean('Active')

    @staticmethod
    def default_active():
        return True

    @classmethod
    def __setup__(cls):
        super(Client, cls).__setup__()
        cls._sql_constraints += [
            ('uuid_uniq', 'UNIQUE(uuid)',
                'The UUID of the client must be unique.'),
        ]

    @staticmethod
    def default_uuid():
        return str(uuid.uuid4())


class Artist(ModelSQL, ModelView):
    'Artist'
    __name__ = 'artist'
    name = fields.Char(
        'Name', required=True, select=True, states=STATES, depends=DEPENDS)
    code = fields.Char(
        'Code', required=True, select=True, states={
            'readonly': True,
        }, help='The unique code of the artist')
    party = fields.Many2One(
        'party.party', 'Party', states=STATES, depends=DEPENDS,
        help='The legal person or organization acting the artist')
    group = fields.Boolean(
        'Group', states={
            'readonly': Or(
                ~Eval('active'),
                Bool(Eval('group_artists')),
                Bool(Eval('solo_artists')),
            ),
        }, depends=DEPENDS + ['group_artists', 'solo_artists'],
        help='Check, if artist is a group of other artists, '
        'otherwise the artist is a solo artist')
    solo_artists = fields.Many2Many(
        'artist-artist', 'group_artist', 'solo_artist',
        'Solo Artists', domain=[
            ('group', '=', False),
        ], states={
            'readonly': ~Eval('active'),
            'invisible': ~Eval('group'),
        }, depends=['active', 'group'],
        help='The membering solo artists of this group')
    group_artists = fields.Many2Many(
        'artist-artist', 'solo_artist', 'group_artist',
        'Group Artists', domain=[
            ('group', '=', True),
        ], states={
            'readonly': ~Eval('active'),
            'invisible': Bool(Eval('group')),
        }, depends=['active', 'group'],
        help='The groups this solo artist is member of')
    access_parties = fields.Function(
        fields.Many2Many(
            'party.party', None, None, 'Access Parties',
            help='Shows the collection of all parties with access '
            'permissions to this artist'),
        'get_access_parties')
    invitation_token = fields.Char(
        'Invitation Token', help='The invitation token of a web user '
        'to claim this artist')
    description = fields.Text(
        'Description', states=STATES, depends=DEPENDS,
        help='A description of the artist')
    picture_data = fields.Binary(
        'Picture Data', states=STATES, depends=DEPENDS,
        help='Picture data of a photograph or logo')
    picture_data_mime_type = fields.Char(
        'Picture Data Mime Type', states=STATES, depends=DEPENDS,
        help='The mime type of picture data.')
    payee = fields.Many2One(
        'party.party', 'Payee',
        domain=[('id', 'in', Eval('access_parties', []))],
        states={
            'readonly': Or(
                ~Eval('active'),
                Bool(Eval('valid_payee')),
            ),
        },
        depends=DEPENDS + ['access_parties', 'group_artists', 'solo_artists'],
        help='The actual payee party of this artist which is '
        'responsible for earnings of this artist')
    payee_proposal = fields.Many2One(
        'party.party', 'Payee Proposal',
        domain=[('id', 'in', Eval('access_parties', []))],
        states=STATES, depends=DEPENDS + ['access_parties'],
        help='The proposed payee party of this artist')
    payee_acceptances = fields.Many2Many(
        'artist.payee.acceptance', 'artist', 'party', 'Payee Acceptances',
        domain=[('id', 'in', Eval('access_parties', []))],
        states=STATES, depends=DEPENDS + ['access_parties'],
        help='The parties which accepts the payee proposal')
    valid_payee = fields.Boolean(
        'Valid Payee', states={
            'readonly': Or(
                ~Eval('active'),
                ~Bool(Eval('payee')),
            ),
        }, depends=DEPENDS + ['payee'],
        help='Check, if the payee is manually validated by '
        'administration.')
    bank_account_number = fields.Many2One(
        'bank.account.number', 'Bank Account Number', states={
            'readonly': ~Bool(Eval('payee'))},
        domain=[('id', 'in', Eval('bank_account_numbers'))],
        depends=['payee', 'bank_account_numbers'],
        help='The bank account number for this artist')
    bank_account_numbers = fields.Function(
        fields.Many2Many(
            'bank.account.number', None, None, 'Bank Account Numbers',
            help='Shows the collection of all available bank account '
            'numbers of this artist'),
        'on_change_with_bank_account_numbers')
    bank_account_owner = fields.Function(
        fields.Many2One(
            'party.party', 'Bank Account Owner', states={
                'readonly': (
                    Or(
                        ~Bool(Eval('payee')),
                        ~Bool(Eval('bank_account_number'))))},
            help='Shows the bank account owner for this artist',
            depends=['payee', 'bank_account_number']),
        'on_change_with_bank_account_owner')
    hat_account = fields.Property(
        fields.Many2One(
            'account.account', 'Hat Account', domain=[
                ('kind', '=', 'hat'),
                ('company', '=', Eval('context', {}).get('company', -1)),
            ], states={
                'required': Bool(Eval('context', {}).get('company')),
                'invisible': ~Eval('context', {}).get('company'),
            }))
    currency_digits = fields.Function(
        fields.Integer('Currency Digits'), 'get_currency_digits')
    hat_balance = fields.Function(
        fields.Numeric(
            'Hat Account Balance',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_hat_balance', searcher='search_hat_balance')
    active = fields.Boolean('Active')

    @classmethod
    def __setup__(cls):
        super(Artist, cls).__setup__()
        cls._sql_constraints = [
            ('code_uniq', 'UNIQUE(code)',
             'The code of the Artist must be unique.'),
            ('invitation_token_uniq', 'UNIQUE(invitation_token)',
                'The invitation token of the artist must be unique.'),
        ]
        cls._error_messages.update(
            {
                'wrong_name': (
                    'Invalid Artist name "%%s": You can not use '
                    '"%s" in name field.' % SEPARATOR),
            })
        cls._order.insert(1, ('name', 'ASC'))

    @staticmethod
    def default_invitation_token():
        return str(uuid.uuid4())

    @classmethod
    def validate(cls, artists):
        super(Artist, cls).validate(artists)
        for artist in artists:
            artist.check_name()

    def check_name(self):
        if SEPARATOR in self.name:
            self.raise_user_error('wrong_name', (self.name,))

    @staticmethod
    def order_code(tables):
        table, _ = tables[None]
        return [CharLength(table.code), table.code]

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_payee_validation_state():
        return 'accepted'

    @classmethod
    def get_access_parties(cls, artists, name):
        parties = {}
        for artist in artists:
            parties[artist.id] = []
            if artist.party:
                parties[artist.id] += [artist.party.id]
            if artist.solo_artists:
                for solo_artist in artist.solo_artists:
                    if solo_artist.party:
                        parties[artist.id] += [solo_artist.party.id]
        return parties

    @fields.depends('party', 'access_parties')
    def on_change_with_bank_account_numbers(self, name=None):
        BankAccountNumber = Pool().get('bank.account.number')

        bank_account_numbers = []
        numbers = BankAccountNumber.search(
            [
                'OR', [
                    (
                        'account.owner.id', 'in', [
                            p.id for p in self.access_parties])
                ], [
                    ('account.owner.id', '=', self.party.id
                        if self.party else None),
                ]
            ])
        if numbers:
            bank_account_numbers = [n.id for n in numbers]
        else:
            bank_account_numbers = None
        return bank_account_numbers

    @fields.depends('bank_account_number')
    def on_change_with_bank_account_owner(self, name=None):
        if self.bank_account_number:
            bank_account_owner = (
                self.bank_account_number.account.owner.id)
        else:
            bank_account_owner = None
        return bank_account_owner

    @fields.depends('payee')
    def on_change_payee(self):
        changes = {}
        if self.payee:
            changes = {
                'payee_acceptances': {
                    'remove': [
                        a.id for a in self.payee_acceptances]},
                'valid_payee': False,
                'payee_proposal': None}
        return changes

    @fields.depends('payee_proposal')
    def on_change_payee_proposal(self):
        changes = {}
        if self.payee_proposal:
            changes = {
                'payee_acceptances': {
                    'remove': [
                        a.id for a in self.payee_acceptances]},
                'valid_payee': False}
        return changes

    @classmethod
    def get_hat_balance(cls, artists, names):
        WebUser = Pool().get('web.user')

        result = WebUser.get_balance(items=artists, names=names)
        return result

    def get_currency_digits(self, name):
        Company = Pool().get('company.company')
        if Transaction().context.get('company'):
            company = Company(Transaction().context['company'])
            return company.currency.digits
        return 2

    @classmethod
    def search_hat_balance(cls, name, clause):
        WebUser = Pool().get('web.user')

        result = WebUser.search_balance(name, clause)
        return result

    @classmethod
    def create(cls, vlist):
        Sequence = Pool().get('ir.sequence')
        Configuration = Pool().get('collecting_society.configuration')

        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if not values.get('code'):
                config = Configuration(1)
                values['code'] = Sequence.get_id(config.artist_sequence.id)
        return super(Artist, cls).create(vlist)

    @classmethod
    def copy(cls, artists, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['code'] = None
        return super(Artist, cls).copy(artists, default=default)

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            'OR',
            ('code',) + tuple(clause[1:]),
            ('name',) + tuple(clause[1:]),
        ]


class ArtistArtist(ModelSQL):
    'Artist - Artist'
    __name__ = 'artist-artist'
    group_artist = fields.Many2One(
        'artist', 'Group Artist', required=True, select=True)
    solo_artist = fields.Many2One(
        'artist', 'Solo Artist', required=True, select=True)


class ArtistPayeeAcceptance(ModelSQL):
    'Artist Payee Acceptance'
    __name__ = 'artist.payee.acceptance'
    artist = fields.Many2One(
        'artist', 'Artist', required=True, select=True, ondelete='CASCADE')
    party = fields.Many2One(
        'party.party', 'Party', required=True, select=True, ondelete='CASCADE')


class Identifier(ModelSQL, ModelView):
    'Identifier'
    __name__ = 'creation.identification.identifier'
    _rec_name = 'identifier'
    identification = fields.Many2One(
        'creation.identification', 'Identification',
        help='The identification of a creation for this identifier')
    identifier = fields.Text('Identifier')


class Identification(ModelSQL, ModelView):
    'Identification'
    __name__ = 'creation.identification'
    identifiers = fields.One2Many(
        'creation.identification.identifier', 'identification', 'Identifiers',
        help='The identifiers of the creation')
    creation = fields.Many2One(
        'creation', 'Creation', help='The creation identified by '
        'the identifiers')
    id3 = fields.Text('ID3', help='ID3 tag')

    def get_rec_name(self, name):
        return (self.creation.title if self.creation else 'unknown')


class Creation(ModelSQL, ModelView):
    'Creation'
    __name__ = 'creation'
    title = fields.Char(
        'Title', required=True, select=True, states=STATES, depends=DEPENDS,
        help='The title or name of the creation')
    code = fields.Char(
        'Code', required=True, select=True, states={
            'readonly': True,
        }, help='The identification code for the creation')
    artist = fields.Many2One(
        'artist', 'Artist', states=STATES, depends=DEPENDS, help='The named '
        'artist for the creation')
    contributions = fields.One2Many(
        'creation.contribution', 'creation', 'Contributions', states=STATES,
        depends=DEPENDS, help='All individual contributions to the creation '
        'like composition and lyric creators, band members and singer/solo '
        'artists and their role.')
    licenses = fields.One2Many(
        'creation.license', 'creation', 'Licenses', states=STATES,
        depends=DEPENDS)
    identifiers = fields.One2Many(
        'creation.identification', 'creation', 'Identifiers',
        states=STATES, depends=DEPENDS)
    derivative_relations = fields.One2Many(
        'creation.original.derivative', 'original_creation',
        'Derived Relations', states=STATES, depends=DEPENDS,
        help='All creations deriving from the actual creation')
    original_relations = fields.One2Many(
        'creation.original.derivative', 'derivative_creation',
        'Originating Relations', states=STATES, depends=DEPENDS,
        help='All creations originating the actual creation')
    state = fields.Selection(
        [
            ('on_approval', 'On Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ], 'State', states=STATES, depends=DEPENDS)
    active = fields.Boolean('Active')

    @classmethod
    def __setup__(cls):
        super(Creation, cls).__setup__()
        cls._sql_constraints = [
            ('code_uniq', 'UNIQUE(code)',
             'The code of the creation must be unique.')
        ]
        cls._order.insert(1, ('title', 'ASC'))

    @staticmethod
    def order_code(tables):
        table, _ = tables[None]
        return [CharLength(table.code), table.code]

    @staticmethod
    def default_state():
        return 'on_approval'

    @staticmethod
    def default_active():
        return True

    def get_rec_name(self, name):
        result = '[%s] %s' % (
            self.artist.name if self.artist and self.artist.name
            else '<unknown artist>',
            self.title if self.title else '<unknown title>')
        return result

    @classmethod
    def create(cls, vlist):
        Sequence = Pool().get('ir.sequence')
        Configuration = Pool().get('collecting_society.configuration')

        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if not values.get('code'):
                config = Configuration(1)
                values['code'] = Sequence.get_id(config.creation_sequence.id)
        return super(Creation, cls).create(vlist)

    @classmethod
    def copy(cls, creations, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['code'] = None
        return super(Creation, cls).copy(creations, default=default)

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            'OR',
            ('code',) + tuple(clause[1:]),
            ('title',) + tuple(clause[1:]),
        ]


class CreationOriginalDerivative(ModelSQL, ModelView):
    'Creation - Original - Derivative'
    __name__ = 'creation.original.derivative'
    original_creation = fields.Many2One(
        'creation', 'Original Creation', select=True, required=True)
    derivative_creation = fields.Many2One(
        'creation', 'Derivative Creation', select=True, required=True)
    allocation_type = fields.Selection(
        [
            (None, ''),
            ('adaption', 'Adaption'),
            ('cover', 'Cover'),
            ('remix', 'Remix'),
        ], 'Allocation Type', required=True, sort=False,
        help='The allocation type of the actual creation in the relation '
        'from its origins or towards its derivatives\n'
        '*Adaption*: \n'
        '*Cover*: \n'
        '*Remix*: \n')


class CreationContribution(ModelSQL, ModelView):
    'Creation Contribution'
    __name__ = 'creation.contribution'

    creation = fields.Many2One(
        'creation', 'Creation', required=True, select=True)
    artist = fields.Many2One(
        'artist', 'Artist', help='The involved artist contributing to the '
        'creation')
    type = fields.Selection(
        [
            ('performance', 'Performance'),
            ('composition', 'Composition'),
            ('text', 'Text'),
        ], 'Type', required=True,
        help='The type of contribution of the artist.\n\n'
        '*performer*: The artist contributes a performance.\n'
        '*composer*: The artist contributes a composition.\n'
        '*writer*: The artist contributes text.')
    roles = fields.Many2Many(
        'creation.contribution-creation.role', 'contribution', 'role',
        'Roles',
        help='The roles the artist takes in this creation')
    roles_list = fields.Function(
        fields.Char('Roles List'), 'on_change_with_roles_list')

    @fields.depends('roles')
    def on_change_with_roles_list(self, name=None):
        roles = ''
        for role in self.roles:
            roles += '%s, ' % role.name
        return roles.rstrip(', ')

    def get_rec_name(self, name):
        result = '[%s] %s' % (
            self.type, self.creation.title)
        return result


class CreationRole(ModelSQL, ModelView):
    'Roles'
    __name__ = 'creation.role'

    name = fields.Char(
        'Name', required=True, translate=True, help='The name of the role')
    description = fields.Text(
        'Description', translate=True, help='The description of the role')


class ContributionRole(ModelSQL):
    'Contribution - Role'
    __name__ = 'creation.contribution-creation.role'

    contribution = fields.Many2One(
        'creation.contribution', 'Contribution', required=True, select=True)
    role = fields.Many2One('creation.role', 'Role', required=True, select=True)


class License(ModelSQL, ModelView):
    'License'
    __name__ = 'license'
    name = fields.Char('Name', required=True, select=True)
    code = fields.Char('Code', required=True, select=True)

    @classmethod
    def __setup__(cls):
        super(License, cls).__setup__()
        cls._sql_constraints = [
            ('code_uniq', 'UNIQUE(code)',
             'The code of the license must be unique.')
        ]
        cls._order.insert(1, ('name', 'ASC'))

    @staticmethod
    def order_code(tables):
        table, _ = tables[None]
        return [CharLength(table.code), table.code]

    @classmethod
    def copy(cls, licenses, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['code'] = None
        return super(License, cls).copy(licenses, default=default)

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            'OR',
            ('code',) + tuple(clause[1:]),
            ('name',) + tuple(clause[1:]),
        ]


class CreationLicense(ModelSQL, ModelView):
    'Creation - License'
    __name__ = 'creation.license'
    creation = fields.Many2One('creation', 'Creation', required=True)
    license = fields.Many2One('license', 'License', required=True)


class Distribution(ModelSQL, ModelView):
    'Distribution'
    __name__ = 'distribution'
    _rec_name = 'code'
    code = fields.Char(
        'Code', required=True, select=True, states={
            'readonly': True,
        })
    date = fields.Date(
        'Distribution Date', required=True, select=True,
        help='The date of the distribution')
    from_date = fields.Date(
        'From Date',
        help='Include utilisations equal or after from date')
    thru_date = fields.Date(
        'Thru Date', help='Include utilisations until thru date')
    allocations = fields.One2Many(
        'distribution.allocation', 'distribution', 'Allocations',
        help='All allocations in this distributon')

    @classmethod
    def __setup__(cls):
        super(Distribution, cls).__setup__()
        cls._sql_constraints = [
            ('code_uniq', 'UNIQUE(code)',
             'The code of the distribution must be unique.')
        ]
        cls._order.insert(1, ('date', 'ASC'))

    @staticmethod
    def order_code(tables):
        table, _ = tables[None]
        return [CharLength(table.code), table.code]

    @staticmethod
    def default_date():
        Date = Pool().get('ir.date')
        return Date.today()

    @classmethod
    def create(cls, vlist):
        Sequence = Pool().get('ir.sequence')
        Configuration = Pool().get('collecting_society.configuration')

        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if not values.get('code'):
                config = Configuration(1)
                values['code'] = Sequence.get_id(
                    config.distribution_sequence.id)
        return super(Distribution, cls).create(vlist)

    @classmethod
    def copy(cls, distributions, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['code'] = None
        return super(Distribution, cls).copy(distributions, default=default)

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            'OR',
            ('code',) + tuple(clause[1:]),
            ('date',) + tuple(clause[1:]),
        ]


class Allocation(ModelSQL, ModelView):
    'Allocation'
    __name__ = 'distribution.allocation'
    distribution = fields.Many2One(
        'distribution', 'Distribution', required=True,
        help='The distribution of the allocation')
    type = fields.Selection(
        [
            ('pocket2hats', 'Pocket to Hats'),
            ('hat2pockets', 'Hat to Pockets'),
        ], 'Type', required=True, sort=False, help='The allocation type:\n'
        '*Pocket to Hats*: Allocates amount from a pocket to many hats\n'
        '*Hat to Pockets*: Allocates amount from a hat to many pockets')
    party = fields.Many2One(
        'party.party', 'Party', required=True,
        help='The party which utilises creations')
    currency_digits = fields.Function(
        fields.Integer('Currency Digits'), 'get_currency_digits')
    amount = fields.Numeric(
        'Amount', digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits'], help='The amount to distribute')
    share_amount = fields.Numeric(
        'Share Amount', digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits'], help='The share for each utilisation')
    move_lines = fields.One2Many(
        'account.move.line', 'origin', 'Account Move Lines',
        domain=[('origin', 'like', 'distribution.allocation,%')],
        help='The account move lines of the allocation')
    utilisations = fields.One2Many(
        'creation.utilisation', 'allocation', 'Utilisations',
        help='The allocated utilisations')

    @classmethod
    def __setup__(cls):
        super(Allocation, cls).__setup__()
        cls._order.insert(1, ('distribution', 'ASC'))
        cls._order.insert(2, ('party', 'ASC'))

    @staticmethod
    def default_type():
        return 'pocket2hats'

    def get_currency_digits(self, name):
        Company = Pool().get('company.company')
        if Transaction().context.get('company'):
            company = Company(Transaction().context['company'])
            return company.currency.digits
        return 2


class Utilisation(ModelSQL, ModelView):
    'Utilisation'
    __name__ = 'creation.utilisation'
    timestamp = fields.DateTime(
        'Timestamp', required=True, select=True,
        help='Point in time of utilisation')
    code = fields.Char(
        'Code', required=True, select=True, states={
            'readonly': True,
        }, help='Sequential code number of the utilisation')
    party = fields.Many2One(
        'party.party', 'Utiliser Party',
        help='The party who uses the creation')
    creation = fields.Many2One(
        'creation', 'Creation', required=True,
        help='The work which is used by the utilizer')
    allocation = fields.Many2One(
        'distribution.allocation', 'Allocation',
        help='The allocation of the utilisation')
    state = fields.Selection(
        [
            ('not_distributed', 'Not Distributed'),
            ('processing', 'Distribution in Process'),
            ('distributed', 'Distributed'),
        ], 'State', required=True, sort=False,
        help='The distribution state of the utilisation.\n\n'
        '*Not Distributed*: The default state for newly created '
        'utilisations.\n'
        '*Distribution in Process*: A distribution is in process.\n'
        '*Distributed*: The distribution is finished and an allocation is '
        'created')
    origin = fields.Reference(
        'Origin', [('creation.utilisation.imp', 'IMP')],
        help='The originating data of the use')

    @classmethod
    def __setup__(cls):
        super(Utilisation, cls).__setup__()
        cls._sql_constraints = [
            ('code_uniq', 'UNIQUE(code)',
             'The code of the utilisation must be unique.')
        ]
        cls._order.insert(1, ('timestamp', 'ASC'))

    @staticmethod
    def default_state():
        return 'not_distributed'

    @staticmethod
    def order_code(tables):
        table, _ = tables[None]
        return [CharLength(table.code), table.code]

    def get_rec_name(self, name):
        return '%s: %s' % (self.creation.title, self.creation.artist)

    @classmethod
    def create(cls, vlist):
        Sequence = Pool().get('ir.sequence')
        Configuration = Pool().get('collecting_society.configuration')

        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if not values.get('code'):
                config = Configuration(1)
                values['code'] = Sequence.get_id(
                    config.utilisation_sequence.id)
        return super(Utilisation, cls).create(vlist)

    @classmethod
    def copy(cls, utilisations, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['code'] = None
        return super(Utilisation, cls).copy(utilisations, default=default)

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            'OR',
            ('code',) + tuple(clause[1:]),
            ('timestamp',) + tuple(clause[1:]),
        ]


class UtilisationIMP(ModelSQL, ModelView):
    'Utilisation for IMP'
    __name__ = 'creation.utilisation.imp'
    _rec_name = 'create_date'

    client = fields.Many2One('client', 'Client', help='The used client')
    time_played = fields.DateTime(
        'Time Played',
        help='The client timestamp (format: yyyy-mm-dd HH:MM:SS) of the '
        'utilisation')
    time_submitted = fields.DateTime(
        'Time Submitted',
        help='The client timestamp (format: yyyy-mm-dd HH:MM:SS) of the '
        'utilisation submission')
    fingerprint = fields.Char(
        'Fingerprint', help='Fingerprint hash of the utilisation')
    fingerprinting_algorithm = fields.Char(
        'Algorithm',
        help='Fingerprinting mechanism of the utilisation, e.g. echoprint')
    fingerprinting_version = fields.Char(
        'Version', help='Fingerprinting algorithm version '
        'of the utilisation')
    title = fields.Char(
        'Title', help='Title tag of the utilisation')
    artist = fields.Char(
        'Artist', help='Artist tag of the utilisation')
    release = fields.Char(
        'Release', help='Release or album tag of the utilisation')
    track_number = fields.Char(
        'Track Number', help='Track number tag of the utilisation')
    duration = fields.Char(
        'Duration', help='Duration tag of the utilisation')
    state = fields.Selection(
        [
            ('unidentified', 'Unidentified'),
            ('processing', 'Process Identification'),
            ('identified', 'Identified'),
        ], 'State', required=True, sort=False,
        help='The state identification of the imp utilisation.\n\n'
        '*Unidentified*: The imp utilisation is not yet identified.\n'
        '*Process Identification*: A identification process is running.\n'
        '*Done*: The identification is finished and a general utilisation is '
        'created')
    utilisation = fields.Function(
        fields.Many2One('creation.utilisation', 'Utilisation'),
        'get_utilisation')

    @classmethod
    def __setup__(cls):
        super(UtilisationIMP, cls).__setup__()
        cls._order.insert(0, ('time_submitted', 'DESC'))

    @staticmethod
    def default_time_submitted():
        return datetime.datetime.now()

    @staticmethod
    def default_state():
        return 'unidentified'

    @staticmethod
    def default_title():
        return '<unknown title>'

    @staticmethod
    def default_artist():
        return '<unknown artist>'

    def get_utilisation(self, name):
        Utilisation = Pool().get('creation.utilisation')

        utilisations = Utilisation.search(
            [('origin', '=', 'creation.utilisation.imp,%s' % self.id)],
            limit=1)
        if not utilisations:
            return None
        return utilisations[0].id


class UtilisationIMPIdentifyStart(ModelView):
    'Identify IMP Utilisations Start'
    __name__ = 'creation.utilisation.imp.identify.start'

    from_date = fields.Date(
        'From Date',
        help='The earliest date to identify IMP utilisations')
    thru_date = fields.Date(
        'Thru Date',
        help='The latest date to identify IMP utilisations')

    @staticmethod
    def default_from_date():
        Date = Pool().get('ir.date')
        t = Date.today()
        return datetime.date(t.year, t.month, 1) - relativedelta(months=1)

    @staticmethod
    def default_thru_date():
        Date = Pool().get('ir.date')
        return Date.today() - relativedelta(months=1) + relativedelta(day=31)


class UtilisationIMPIdentify(Wizard):
    "Identify IMP Utilisations"
    __name__ = 'creation.utilisation.imp.identify'

    start = StateView(
        'creation.utilisation.imp.identify.start',
        'collecting_society.'
        'utilisation_imp_identify_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button(
                'Start Identification', 'identify', 'tryton-ok', default=True),
        ])
    identify = StateTransition()

    def transition_identify(self):
        pool = Pool()
        Creation = pool.get('creation')
        Artist = pool.get('artist')
        Utilisation = pool.get('creation.utilisation')
        UtilisationIMP = pool.get('creation.utilisation.imp')

        imp_utilisations = UtilisationIMP.search([
            (
                'time_submitted', '>=', datetime.datetime.combine(
                    self.start.from_date, datetime.time.min)
            ), (
                'time_submitted', '<=', datetime.datetime.combine(
                    self.start.thru_date, datetime.time.max)
            ), ('state', '=', 'unidentified')])

        for imp_util in imp_utilisations:
            UtilisationIMP.write([imp_util], {'state': 'processing'})
            # identify
            # XXX: Add the identification of the fingerprint here
            creation_title = imp_util.title or 'Unknown Creation'
            artist_name = imp_util.artist or 'Unknown Artist'
            # find
            creation = Creation.search([
                ('title', '=', creation_title),
                ('artist.name', '=', artist_name),
            ])
            # create if not exist
            if not creation:
                artist = Artist.search([('name', '=', artist_name)])
                if not artist:
                    artist = Artist.create([{'name': artist_name}])
                artist = artist[0]
                creation = Creation.create([{
                    'title': creation_title,
                    'artist': artist.id,
                }])
            creation = creation[0]
            # create utilisation
            Utilisation.create([{
                'timestamp': imp_util.time_submitted,
                'creation': creation.id,
                'party': imp_util.client.web_user.party.id,
                'origin': '%s,%i' % (
                    UtilisationIMP.__name__, imp_util.id),
            }])
            UtilisationIMP.write([imp_util], {'state': 'identified'})
        return 'end'


class DistributeStart(ModelView):
    'Distribute Start'
    __name__ = 'distribution.distribute.start'

    date = fields.Date(
        'Distribution Date', required=True,
        help='The date of the distribution')
    from_date = fields.Date(
        'From Date', required=True,
        help='The earliest date to distribute utilisations')
    thru_date = fields.Date(
        'Thru Date', required=True,
        help='The latest date to distribute utilisations')

    @staticmethod
    def default_date():
        Date = Pool().get('ir.date')
        return Date.today()

    @staticmethod
    def default_from_date():
        Date = Pool().get('ir.date')
        t = Date.today()
        return datetime.date(t.year, t.month, 1) - relativedelta(months=1)

    @staticmethod
    def default_thru_date():
        Date = Pool().get('ir.date')
        return Date.today() - relativedelta(months=1) + relativedelta(day=31)


class Distribute(Wizard):
    "Distribute"
    __name__ = 'distribution.distribute'

    start = StateView(
        'distribution.distribute.start',
        'collecting_society.distribution_distribute_start_view_form',
        [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button(
                'Start', 'distribute', 'tryton-ok', default=True),
        ])
    distribute = StateTransition()

    def transition_distribute(self):
        pool = Pool()
        Company = pool.get('company.company')
        Distribution = pool.get('distribution')
        Allocation = pool.get('distribution.allocation')
        Utilisation = pool.get('creation.utilisation')
        Account = pool.get('account.account')
        AccountMove = pool.get('account.move')
        AccountJournal = pool.get('account.journal')
        Party = pool.get('party.party')
        Period = pool.get('account.period')

        company = Company(Transaction().context['company'])
        currency = company.currency
        # TODO:
        # * Redistribution
        # * Check if distribution period overlaps with existing distribution

        # Collect utilisations
        utilisations = Utilisation.search([
            (
                'timestamp', '>=', datetime.datetime.combine(
                    self.start.from_date, datetime.time.min)
            ), (
                'timestamp', '<=', datetime.datetime.combine(
                    self.start.thru_date, datetime.time.max)
            ), ('state', '=', 'not_distributed'),
        ])
        if not utilisations:
            return 'end'
        # Create always a new distribution
        distribution, = Distribution.create(
            [
                {
                    'date': self.start.date,
                    'from_date': self.start.thru_date,
                    'thru_date': self.start.thru_date,
                }
            ]
        )

        party_utilisations = defaultdict(list)
        for utilisation in utilisations:
            party_utilisations[utilisation.party.id].append(utilisation)

        account_moves = []
        for party_id, utilisations in party_utilisations.iteritems():
            if not utilisations:
                continue
            party = Party(party_id)
            amount = party.pocket_balance
            if not amount:
                continue

            if party.pocket_budget < party.pocket_balance:
                amount = party.pocket_budget
            amount = currency.round(amount)
            fee_amount = currency.round(amount * Decimal(10) / Decimal(100))
            share_amount = currency.round(
                (amount - fee_amount) / len(utilisations))
            allocation = {
                'party': party_id,
                'distribution': distribution.id,
                'type': 'pocket2hats',
                'amount': amount,
                'share_amount': share_amount,
            }
            # create allocation
            allocation, = Allocation.create([allocation])

            Utilisation.write(
                utilisations,
                {
                    'state': 'processing',
                    'allocation': allocation.id,
                })
            account_move_lines = [{
                # Company fees move line
                'party': company.party.id,
                'artist': None,
                'account': Account.search([('kind', '=', 'revenue')])[0],
                'debit': Decimal(0),
                'credit': fee_amount,
                'state': 'draft',
            }, {
                # Pocket move line
                'party': party.id,
                'artist': None,
                'account': party.pocket_account.id,
                'debit': amount,
                'credit': Decimal(0),
                'state': 'draft',
            }]
            for utilisation in utilisations:
                breakdown = self._allocate(
                    utilisation.creation,
                    share_amount)
                for artist, amount in breakdown.iteritems():
                    account_move_lines += [{
                        # Hat move lines
                        'party': None,
                        'artist': artist.id,
                        'account': artist.hat_account.id,
                        'debit': Decimal(0),
                        'credit': currency.round(amount),
                        'state': 'draft',
                    }]
            period_id = Period.find(company.id, date=self.start.date)
            journal, = AccountJournal.search([('code', '=', 'TRANS')])
            origin = 'distribution.allocation,%s' % (allocation.id)
            account_moves.append({
                'journal': journal.id,
                'origin': origin,
                'date': self.start.date,
                'period': period_id,
                'state': 'draft',
                'lines': [('create', account_move_lines)],
            })
        AccountMove.create(account_moves)
        Utilisation.write(utilisations, {'state': 'distributed'})
        return 'end'

    def _allocate(self, creation, amount, result=None):
        '''
        Allocates an amount to all involved artists of a creation.
        The tree of original creations is traversed and every node creation is
        allocated by the appropriate derivative types.

        Returns a dictionary with artist as key and the sum of amounts
        as value.
        '''
        amount = Decimal(amount)

        if result is None:
            result = Counter()

        if not creation.contributions:
            # Handle creations from unclaimed fingerprinting identification:
            # allocate complete amount to creation artist
            result[creation.artist] = amount
            return result

        composer = [
            c.artist for c in creation.contributions
            if c.type == 'composition']
        texter = [
            c.artist for c in creation.contributions if c.type == 'text']
        performers = [
            c.artist for c in creation.contributions
            if c.type == 'performance']
        creators = composer or texter

        performer_amount = Decimal(0)
        composer_amount = Decimal(0)
        texter_amount = Decimal(0)

        if performers and creators:
            amount = amount / Decimal(2)

        if composer and texter:
            composer_amount = (
                amount * Decimal(65) / Decimal(100) / Decimal(len(composer)))
            texter_amount = (
                amount * Decimal(35) / Decimal(100) / Decimal(len(texter)))
        elif texter:
            texter_amount = amount / Decimal(len(texter))
        elif composer:
            composer_amount = amount / Decimal(len(composer))

        if performers:
            performer_amount = amount / Decimal(len(performers))

        for c in composer:
            result[c] += composer_amount
        for t in texter:
            result[t] += texter_amount
        for p in performers:
            result[p] += performer_amount

#    # Traverse Originators
#    for original in creation.original_creations:
#        if not original.derivative_type:
#            result = allocate(
#                creation=original.original_creation,
#                amount=amount / Decimal(len(creation.original_creations)),
#                result=result)
        return result
