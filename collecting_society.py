# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society
import os
import uuid
import datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from collections import Counter, defaultdict
from sql.functions import CharLength
import hurry.filesize

from trytond.model import ModelView, ModelSQL, fields
from trytond.wizard import Wizard, StateView, Button, StateTransition

from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.pyson import Eval, Bool, Or, And


__all__ = [

    # Creative
    'Artist',
    'ArtistArtist',
    'ArtistPayeeAcceptance',
    'License',
    'Creation',
    'CreationLicense',
    'CreationOriginalDerivative',
    'CreationContribution',
    'CreationContent',
    'Label',
    'Release',
    'CreationRelease',
    'Genre',
    'ReleaseGenre',
    'CreationRole',
    'ContributionRole',

    # Archive
    'ContainerLabel',
    'ArchiveLabel',
    'Container',
    'Archive',
    'Storehouse',
    'Harddisk',
    'Filesystem',
    'HarddiskTest',
    # 'Uuid',
    'Checksum',
    'Content',

    # Accounting,
    'Allocation',
    'Utilisation',
    'Distribution',
    'DistributeStart',
    'Distribute',

    # Events
    'Client',
    'Identifier',
    'Identification',
    'Fingerprintlog',

    # Adore
    'UtilisationIMP',
    'UtilisationIMPIdentifyStart',
    'UtilisationIMPIdentify',

    # Tryton
    'STATES',
    'DEPENDS',

]
STATES = {
    'readonly': ~Eval('active'),
}
DEPENDS = ['active']
SEPARATOR = u' /25B6 '


##############################################################################
# Creative
##############################################################################


class Artist(ModelSQL, ModelView):
    'Artist'
    __name__ = 'artist'
    _history = True
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
    _history = True
    group_artist = fields.Many2One(
        'artist', 'Group Artist', required=True, select=True)
    solo_artist = fields.Many2One(
        'artist', 'Solo Artist', required=True, select=True)


class ArtistPayeeAcceptance(ModelSQL):
    'Artist Payee Acceptance'
    __name__ = 'artist.payee.acceptance'
    _history = True
    artist = fields.Many2One(
        'artist', 'Artist', required=True, select=True, ondelete='CASCADE')
    party = fields.Many2One(
        'party.party', 'Party', required=True, select=True, ondelete='CASCADE')


class License(ModelSQL, ModelView):
    'License'
    __name__ = 'license'
    _history = True
    name = fields.Char('Name', required=True, select=True)
    code = fields.Char('Code', required=True, select=True)
    freedom_rank = fields.Integer('Freedom Rank')

    @classmethod
    def __setup__(cls):
        super(License, cls).__setup__()
        cls._sql_constraints = [
            ('code_uniq', 'UNIQUE(code)',
             'The code of the license must be unique.')
        ]
        cls._order.insert(1, ('freedom_rank', 'ASC'))

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


class Creation(ModelSQL, ModelView):
    'Creation'
    __name__ = 'creation'
    _history = True
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
    default_license = fields.Function(
        fields.Many2One('license', 'Default License'),
        'get_default_license', searcher='search_default_license')
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
    releases = fields.One2Many(
        'creation.release', 'creation', 'Releases',
        help='The releases of this creation.')
    time = fields.Char('Time', help='The playing time of the creation.')
    genres = fields.Many2Many(
        'release.genre', 'release', 'genre', 'Genres',
        help='The genres of the creation.')

    state = fields.Selection(
        [
            ('on_approval', 'On Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ], 'State', states=STATES, depends=DEPENDS)
    content = fields.One2One(
        'creation-content', 'creation', 'content',  'Content',
        help='The content of the creation.')
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

    def get_default_license(self, name):
        default = None
        for creationlicense in self.licenses:
            license = creationlicense.license
            if not default or license.freedom_rank > default.freedom_rank:
                default = license
        return default.id

    def search_default_license(self, name):
        return self.get_default_license(name)

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


class CreationLicense(ModelSQL, ModelView):
    'Creation - License'
    __name__ = 'creation.license'
    _history = True
    creation = fields.Many2One('creation', 'Creation', required=True)
    license = fields.Many2One('license', 'License', required=True)


class CreationContent(ModelSQL, ModelView):
    'Creation - Content'
    __name__ = 'creation-content'
    _history = True
    creation = fields.Many2One(
        'creation', 'Creation', ondelete='CASCADE', select=True, required=True)
    content = fields.Many2One(
        'content', 'Content', ondelete='CASCADE', select=True, required=True)

    @classmethod
    def __setup__(cls):
        super(CreationContent, cls).__setup__()
        cls._sql_constraints = [
            ('creation_uniq', 'UNIQUE("creation")',
                'Error!\n'
                'A creation can only be linked to one and only one content.\n'
                'The used creation is already linked to another content.'),
            ('content_uniq', 'UNIQUE("content")',
                'Error!\n'
                'A content can only be linked to one and only one creation.\n'
                'The used content is already linked to another creation.'),
        ]


class Label(ModelSQL, ModelView):
    'Label'
    __name__ = 'label'
    _history = True

    name = fields.Char('Name', help='The name of the label.')
    party = fields.Many2One(
        'party.party', 'Party', help='The legal party of the label')
    gvl_code = fields.Char(
        'GVL Code', help='The label code of the german '
        '"Gesellschaft zur Verwertung von Leistungsschutzrechten" (GVL)')


class Release(ModelSQL, ModelView):
    'Release'
    __name__ = 'release'
    _history = True
    _rec_name = 'title'

    title = fields.Char('Title')
    creations = fields.One2Many(
        'creation.release', 'release', 'Creations',
        help='The creations included in the release')
    neighbouring_rights_society = fields.Many2One(
        'party.party', 'Neighbouring Rights Society',
        help='Representing collecting society/PRO for neighbouring rights.'
    )  # -1
    label = fields.Many2One(
        'label', 'Label', help='The lable of the release.')
    ean_upc_code = fields.Integer('EAN/UPC Code', help='The EAN/UPC Code')
    number_mediums = fields.Integer(
        'Number of Mediums', help='The number of mediums.')
    label_order_number = fields.Char(
        'Label Order Number', help='The label order number.')
    release_date = fields.Date('Release Date', help='Date of (first) release.')
    release_cancellation_date = fields.Date(
        'Release Cancellation Date', help='Date of release cancellation')  # -1
    online_release_date = fields.Date(
        'Online Release Date', help='The Date of digital online release.')
    online_cancellation_date = fields.Date(
        'Online Cancellation Date',
        help='Date of online release cancellation.')  # -1
    copyright_date = fields.Date(
        'Copyright Date', help='Date of the copyright.')
    copyright_owner = fields.Many2One(
        'party.party', 'Copyright Owner', help='Copyright owning party.')
    production_date = fields.Date(
        'Production Date', help='Date of production.')  # -1
    producer = fields.Many2One('party.party', 'Producer')  # -1
    genres = fields.Many2Many(
        'release.genre', 'release', 'genre', 'Genres',
        help='The genres of the release.')
    distribution_territory = fields.Char(
        'Distribution Territory')  # many2one, -1
    isrc_code = fields.Char(
        'ISRC Code',
        help='The International Standard Recording Code of the release')
    warning = fields.Char(
        'Warning', help='A warning note for this release.')  # many2one, -1


class CreationRelease(ModelSQL, ModelView):
    'Creation Release'
    __name__ = 'creation.release'
    _history = True

    creation = fields.Many2One(
        'creation', 'Creation', required=True)
    release = fields.Many2One(
        'release', 'Release', required=True)
    medium_number = fields.Integer(
        'Medium Number', help=u'The number of the medium on CD, LP, ...')
    track_number = fields.Integer(
        'Track Number', help='Track number on the medium')


class Genre(ModelSQL, ModelView):
    'Genre'
    __name__ = 'genre'
    _history = True

    name = fields.Char('Name', help='The name of the genre.')
    description = fields.Text(
        'Description', help='The description of the genre.')


class ReleaseGenre(ModelSQL):
    'Release - Genre'
    __name__ = 'release.genre'
    _history = True

    release = fields.Many2One(
        'release', 'Release', required=True, select=True)
    genre = fields.Many2One(
        'genre', 'Genre', required=True, select=True)


class CreationOriginalDerivative(ModelSQL, ModelView):
    'Creation - Original - Derivative'
    __name__ = 'creation.original.derivative'
    _history = True

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
    _history = True

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
    composition_copyright_date = fields.Date(
        'Composition Copyright Date')
    composition_copyright_owner = fields.Many2One(
        'party.party', 'Composition Copyright Owner')
    composition_license = fields.Many2One(
        'creation.license', 'License')
    composition_publishing_date = fields.Date(
        'Composition Publishing Date')
    composition_publisher = fields.Many2One(
        'party.party', 'Composition Publisher',
        help='Composition Publishing Entity')
    lyrics_copyright_date = fields.Date(
        'Lyrics Copyright Date')
    lyrics_copyright_artist = fields.Many2One(
        'artist', 'Lyrics Copyright Artist')
    lyrics_license = fields.Many2One(
        'creation.license', 'License')
    lyrics_publishing_date = fields.Date(
        'Lyrics Publishing Date')
    lyrics_publisher = fields.Many2One(
        'party.party', 'Lyrics Publisher', help='Lyrics Publishing Entity')
    collecting_society = fields.Many2One(
        'party.party', 'Collecting Society')

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
    _history = True

    name = fields.Char(
        'Name', required=True, translate=True, help='The name of the role')
    description = fields.Text(
        'Description', translate=True, help='The description of the role')


class ContributionRole(ModelSQL):
    'Contribution - Role'
    __name__ = 'creation.contribution-creation.role'
    _history = True

    contribution = fields.Many2One(
        'creation.contribution', 'Contribution', required=True, select=True)
    role = fields.Many2One('creation.role', 'Role', required=True, select=True)


##############################################################################
# Archive
##############################################################################


class ContainerLabel(ModelSQL, ModelView):
    'Container Label'
    __name__ = 'container.label'
    _history = True
    code = fields.Char(
        'Code', required=True, select=True, states={
            'readonly': True,
        }, help='The Label code for the Containers.')
    containers = fields.One2Many(
        'container', 'label', 'Container',
        help='The Containers with this Label.')

    @staticmethod
    def order_code(tables):
        table, _ = tables[None]
        return [CharLength(table.code), table.code]

    @classmethod
    def create(cls, vlist):
        Sequence = Pool().get('ir.sequence')
        Configuration = Pool().get('collecting_society.configuration')

        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if not values.get('code'):
                config = Configuration(1)
                values['code'] = Sequence.get_id(
                    config.container_label_sequence.id)
        return super(ContainerLabel, cls).create(vlist)

    @classmethod
    def copy(cls, creations, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['code'] = None
        return super(ContainerLabel, cls).copy(creations, default=default)


class ArchiveLabel(ModelSQL, ModelView):
    'Archive Label'
    __name__ = 'archive.label'
    _history = True
    code = fields.Char(
        'Code', required=True, select=True, states={
            'readonly': True,
        }, help='The Label code for the Archives.')
    archives = fields.One2Many(
        'archive', 'label', 'Archives',
        help="The Archives with this Label.")

    @staticmethod
    def order_code(tables):
        table, _ = tables[None]
        return [CharLength(table.code), table.code]

    @classmethod
    def create(cls, vlist):
        Sequence = Pool().get('ir.sequence')
        Configuration = Pool().get('collecting_society.configuration')

        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if not values.get('code'):
                config = Configuration(1)
                values['code'] = Sequence.get_id(
                    config.archive_label_sequence.id)
        return super(ArchiveLabel, cls).create(vlist)

    @classmethod
    def copy(cls, creations, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['code'] = None
        return super(ArchiveLabel, cls).copy(creations, default=default)


class Container(ModelSQL, ModelView):
    'Container'
    __name__ = 'container'
    _history = True
    label = fields.Many2One(
        'container.label', 'Label', required=True,
        help='The Label of the Container.')
    storehouse = fields.Many2One(
        'storehouse', 'Storehouse', required=True,
        help='The Storehouse of the Container.')
    storage = fields.Reference(
        'Storage', [('harddisk', 'Harddisk')], required=True,
        help='The physical realization of the Container.')
    version = fields.Integer(
        'Version', required=True,
        help='The version of the Container Label.')
    location = fields.Char(
        'Location', help='The local position of the Container.')
    closed = fields.Boolean(
        'Closed', help='The finalization state of the Container.')


class Archive(ModelSQL, ModelView):
    'Archive'
    __name__ = 'archive'
    _history = True
    label = fields.Many2One(
        'archive.label', 'Label', required=True,
        help='The Label of the Archive.')
    storage = fields.Reference(
        'Storage', [('harddisk.filesystem', 'Filesystem')], required=True,
        help='The physical realization of the Archive.')
    contents = fields.One2Many(
        'content', 'archive', 'Contents', help='The Contents of the Archive.')
    closed = fields.Boolean(
        'Closed', help='The finalization state of the Archive.')


class Storehouse(ModelSQL, ModelView):
    'Storehouse'
    __name__ = 'storehouse'
    _history = True
    code = fields.Char(
        'Code', required=True,
        help='The Code of the Storehouse.')
    user = fields.Many2One(
        'res.user', 'User', required=True,
        help='The admin user of the Storehouse.')
    containers = fields.One2Many(
        'container', 'storehouse', 'Containers',
        help='The containers in the Storehouse.')


class Harddisk(ModelSQL, ModelView):
    'Harddisk'
    __name__ = 'harddisk'
    _history = True
    container = fields.Function(
        fields.Many2One('container', 'Container'), 'get_container')
    raid_type = fields.Char(
        'Raid Type', required=True,
        help='The type of the Raid.')
    raid_number = fields.Char(
        'Raid Number', required=True,
        help='The current number of the harddisk in the Raid.')
    raid_total = fields.Char(
        'Raid Total', required=True,
        help='The total number of harddisks in the Raid.')
    filesystems = fields.One2Many(
        'harddisk.filesystem', 'harddisk', 'Filesystems',
        help='The Filesystems on the Harddisk.')
    uuid_host = fields.Char(
        'Uuid Host', required=True, help='The uuid of the Host.')
    uuid_harddisk = fields.Char(
        'Uuid Harddisk', required=True, help='The uuid of the Harddisk.')
    checksum_harddisk = fields.Many2One(
        'checksum', 'Checksum Harddisk',
        help='The Checksum of the Harddisk.')
    tests = fields.One2Many(
        'harddisk.test', 'harddisk', 'Integrity Tests',
        help='The integrity tests of the Harddisk.')
    user = fields.Many2One(
        'res.user', 'User', required=True,
        help='The admin user of the Storehouse.')
    online = fields.Boolean(
        'Online', help='The online status of the harddisk.')
    state = fields.Selection(
        [
            ('setup', 'Setup'),
            ('in_use', 'In Use'),
            ('out_of_order', 'Out of Order'),
        ], 'State', required=True, sort=False,
        help='The usage state of the Harddisk.')
    # closed = fields.Function(container.closed)
    # status = fields.Function(status of last harddisk test)
    # sticker_text = fields.Function(text of sticker)
    # sticker_pdf = fields.Function(pdf of sticker)

    def get_container(self, name):
        Container = Pool().get('container')
        container = Container.search(
            [('storage', '=', 'harddisk,%s' % self.id)], limit=1)
        if not container:
            return None
        return container[0].id


class Filesystem(ModelSQL, ModelView):
    'Filesystem'
    __name__ = 'harddisk.filesystem'
    _history = True
    archive = fields.Function(
        fields.Many2One('archive', 'Archive'), 'get_archive')
    harddisk = fields.Many2One(
        'harddisk', 'Harddisk', required=True,
        help='The Harddisk on which the filesystem resides.')
    uuid_partition = fields.Char(
        'Uuid Partition', required=True, help='The uuid of the Partition.')
    uuid_raid = fields.Char(
        'Uuid Raid', required=True, help='The uuid of the Raid.')
    uuid_raid_sub = fields.Char(
        'Uuid Raid Sub', required=True, help='The uuid of the Raid Sub.')
    uuid_crypto = fields.Char(
        'Uuid Crypto', required=True, help='The uuid of the Crypto.')
    uuid_lvm = fields.Char(
        'Uuid Lvm', required=True, help='The uuid of the Lvm.')
    uuid_filesystem = fields.Char(
        'Uuid Filesystem', required=True, help='The uuid of the Filesystem.')
    checksum_partition = fields.Many2One(
        'checksum', 'Checksum',
        help='The Checksum of the Partition.')
    checksum_raid = fields.Many2One(
        'checksum', 'Checksum',
        help='The Checksum of the Raid.')
    checksum_raid_sub = fields.Many2One(
        'checksum', 'Checksum',
        help='The Checksum of the Raid Sub.')
    checksum_crypto = fields.Many2One(
        'checksum', 'Checksum',
        help='The Checksum of the Crypto.')
    checksum_lvm = fields.Many2One(
        'checksum', 'Checksum',
        help='The Checksum of the Lvm.')
    checksum_filesystem = fields.Many2One(
        'checksum', 'Checksum',
        help='The Checksum of the Filesystem.')
    partition_number = fields.Integer(
        'Partition Number', required=True,
        help='The number of the partition on the Harddisk.')
    # closed = fields.Function(archive.closed)

    def get_container(self, name):
        Archive = Pool().get('archive')
        archive = Archive.search(
            [('storage', '=', 'archive,%s' % self.id)], limit=1)
        if not archive:
            return None
        return archive[0].id


class HarddiskTest(ModelSQL, ModelView):
    'Harddisk Test'
    __name__ = 'harddisk.test'
    _history = True
    harddisk = fields.Many2One(
        'harddisk', 'Harddisk', required=True,
        help='The harddisk which was tested.')
    user = user = fields.Many2One(
        'res.user', 'User', required=True,
        help='The admin user which executed the Test.')
    timestamp = fields.DateTime(
        'Timestamp', required=True,
        help='The point in time of the Test.')
    status = fields.Selection(
        [
            ('sane', 'Sane'),
            ('error_harddisk', 'Harddisk Error'),
            ('error_partition', 'Partition Error'),
            ('error_raid', 'Raid Error'),
            ('error_raid_sub', 'Raid Sub Error'),
            ('error_crypto', 'Crypto Error'),
            ('error_lvm', 'Lvm Error'),
            ('error_filesystem', 'Filesystem Error'),
        ], 'State', required=True, sort=False,
        help='The usage state of the Harddisk.')


# class Uuid(ModelSQL):
#     'Uuid'
#     __name__ = 'uuid'
#     _history = True
#     timestamp = fields.DateTime(
#         'Timestamp', required=True, help='Point in time of Uuid generation.')
#     algorithm = fields.Char(
#         'Algorithm', required=True, help='The Uuid generation algorithm.')
#     code = fields.Text(
#         'Uuid', required=True, help='The Uuid String.')


class Checksum(ModelSQL, ModelView):
    'Checksum'
    __name__ = 'checksum'
    _history = True
    origin = fields.Reference(
        'Origin', [
            ('content', 'Content'),
            ('harddisk', 'Harddisk')
        ],
        help='The originating data of the checksum')
    code = fields.Char(
        'Checksum', required=True, help='The string of the Checksum.')
    timestamp = fields.DateTime(
        'Timestamp', required=True, help='The point in time of the Checksum.')
    algorithm = fields.Char(
        'Algorithm', required=True, help='The algorithm for the Checksum.')
    begin = fields.Integer(
        'Begin', help='The position of the first byte of the Checksum.')
    end = fields.Integer(
        'End', help='The position of the last byte of the Checksum.')


class Content(ModelSQL, ModelView):
    'Content'
    __name__ = 'content'
    _history = True
    uuid = fields.Char(
        'UUID', required=True, help='The uuid of the Content.')
    name = fields.Char(
        'File Name', required=True, help='The name of the file.')
    extension = fields.Function(
        fields.Char('Extension'), 'on_change_with_extension')
    size = fields.BigInteger('Size', help='The size of the content in Bytes.')
    path = fields.Char('Path')
    preview_path = fields.Char('Preview Path')
    mime_type = fields.Char('Mime Type', help='The media or content type.')
    mediation = fields.Boolean('Mediation')
    duplicate_of = fields.Many2One(
        'content', 'Duplicate of',
        domain=[('duplicate_of', '=', None)],
        states={
            'invisible': And(
                Eval('rejection_reason') != 'checksum_collision',
                Eval('rejection_reason') != 'fingerprint_collision'
            )
        }, depends=['rejection_reason'],
        help='The original duplicated Content.')
    duplicates = fields.One2Many(
        'content', 'duplicate_of', 'Duplicates',
        domain=[
            (
                'rejection_reason', 'in',
                ['checksum_collision', 'fingerprint_collision']
            ),
        ], depends=['rejection_reason'],
        help='The original duplicated Content.')
    user = fields.Many2One(
        'res.user', 'User', required=True,
        help='The user which provided the content.')
    fingerprintlogs = fields.One2Many(
        'content.fingerprintlog', 'content', 'Fingerprintlogs')
    checksums = fields.One2Many(
        'checksum', 'origin', 'Checksums',
        help='The checksums of the content.')
    archive = fields.Many2One(
        'archive', 'Archive', help='The Archive of the Content.')
    category = fields.Selection(
        [
            ('audio', 'Audio')
        ], 'Category', required=True, help='The category of content.')
    creation = fields.One2One(
        'creation-content', 'content', 'creation', 'Creation',
        help='The creation of the content.')
    processing_state = fields.Selection(
        [
            ('uploaded', 'Upload finished'),
            ('previewed', 'Preview created'),
            ('checksummed', 'Checksum created'),
            ('fingerprinted', 'Fingerprint created'),
            ('dropped', 'Dropped'),
            ('archived', 'Archived'),
            ('deleted', 'Deleted'),
            ('rejected', 'Rejected'),
            ('unknown', 'Unknown'),
        ], 'State', required=True, help='The processing state of the content.')
    processing_hostname = fields.Char(
        'Processer', states={
            'invisible': Or(
                Eval('processing_state') == 'deleted',
                Eval('processing_state') == 'archived',
                Eval('processing_state') == 'unknown'
            )
        }, depends=['processing_state'],
        help='The hostname of the processing machine.')
    rejection_reason = fields.Selection(
        [
            (None, ''),
            ('checksum_collision', 'Duplicate Checksum'),
            ('fingerprint_collision', 'Duplicate Fingerprint'),
            ('format_error', 'Format Error'),
            ('no_fingerprint', 'No Fingerprint'),
            ('lossy_compression', 'Lossy Compression'),
        ], 'Reason', states={
            'invisible': Eval('processing_state') != 'rejected'
        }, depends=['processing_state'], help='The reason of the rejection.')
    length = fields.Float(
        'Length', digits=(16, 6),
        help='The length or duration of the audio content in seconds [s].',
        states={'invisible': Eval('category') != 'audio'},
        depends=['category'])
    channels = fields.Integer(
        'Channels', help='The number of sound channels.',
        states={'invisible': Eval('category') != 'audio'},
        depends=['category'])
    sample_rate = fields.Integer(
        'Sample Rate', help='Sample rate in Hertz [Hz][1/s].',
        states={'invisible': Eval('category') != 'audio'},
        depends=['category'])
    sample_width = fields.Integer(
        'Sample Width', help='Sample width in Bits.',
        states={'invisible': Eval('category') != 'audio'},
        depends=['category'])

    @classmethod
    def __setup__(cls):
        super(Content, cls).__setup__()
        cls._order.insert(1, ('name', 'ASC'))
        cls._sql_constraints += [
            ('uuid_uniq', 'UNIQUE(uuid)',
                'The UUID of the content must be unique.'),
        ]

    @staticmethod
    def default_category():
        return 'audio'

    @fields.depends('name')
    def on_change_with_extension(self, name=None):
        return os.path.splitext(self.name)[1].lstrip('.')

    def get_currency_digits(self, name):
        Company = Pool().get('company.company')
        if Transaction().context.get('company'):
            company = Company(Transaction().context['company'])
            return company.currency.digits
        return 2

    def get_rec_name(self, name):
        result = '%s: %s %s %s %sHz %sBit' % (
            self.name,
            hurry.filesize.size(self.size, system=hurry.filesize.si)
            if self.size else '0M',
            (
                "{:.0f}:{:02.0f}".format(*divmod(self.length, 60))
                if self.length else '00:00'
            ),
            (
                'none' if self.channels in (None, 0) else
                'mono' if self.channels == 1 else
                'stereo' if self.channels == 2 else
                'multi'
            ),
            self.sample_rate if self.sample_rate else '0',
            self.sample_width if self.sample_width else '0',
        )
        return result


##############################################################################
# Events
##############################################################################


class Client(ModelSQL, ModelView):
    'Client'
    __name__ = 'client'
    _history = True
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


class Identifier(ModelSQL, ModelView):
    'Identifier'
    __name__ = 'creation.identification.identifier'
    _history = True
    _rec_name = 'identifier'
    identification = fields.Many2One(
        'creation.identification', 'Identification',
        help='The identification of a creation for this identifier')
    identifier = fields.Text('Identifier')


class Identification(ModelSQL, ModelView):
    'Identification'
    __name__ = 'creation.identification'
    _history = True
    identifiers = fields.One2Many(
        'creation.identification.identifier', 'identification', 'Identifiers',
        help='The identifiers of the creation')
    creation = fields.Many2One(
        'creation', 'Creation', help='The creation identified by '
        'the identifiers')
    id3 = fields.Text('ID3', help='ID3 tag')

    def get_rec_name(self, name):
        return (self.creation.title if self.creation else 'unknown')


class Fingerprintlog(ModelSQL, ModelView):
    'Fingerprintlog'
    __name__ = 'content.fingerprintlog'
    _history = True
    content = fields.Many2One(
        'content', 'Content', required=True,
        help='The fingerprinted content.')
    user = fields.Many2One(
        'res.user', 'User', required=True,
        help='The user which fingerprinted the content.')
    timestamp = fields.DateTime(
        'Timestamp', required=True, select=True,
        help='Point in time of fingerprinting')
    fingerprinting_algorithm = fields.Char(
        'Algorithm', required=True,
        help='Fingerprinting mechanism of the content, e.g. echoprint')
    fingerprinting_version = fields.Char(
        'Version', required=True,
        help='Fingerprinting algorithm version of the content')


##############################################################################
# Accounting
##############################################################################


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


##############################################################################
# Adore
##############################################################################


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
