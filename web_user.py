# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society
import uuid
import string
import random
from decimal import Decimal

from sql.aggregate import Sum
from sql.conditionals import Coalesce
from sql.operators import Mul

from trytond.model import ModelView, ModelSQL, fields
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Greater
from trytond.rpc import RPC

__all__ = [
    'WebUserRole',
    'WebUser',
    'WebUserResUser',
    'WebUserWebUserRole',
    'WebUserParty',
]
_OPT_IN_STATES = [
    ('new', 'New'),
    ('mail-sent', 'Mail Sent'),
    ('opted-in', 'Opted-In'),
    ('opted-out', 'Opted-Out'),
]


class WebUserRole(ModelSQL, ModelView):
    "Web User Role"
    __name__ = 'web.user.role'
    _history = True

    name = fields.Char(
        'Name', required=True, select=True, translate=True,
        help='The display name of role.')
    code = fields.Char(
        'Code', required=True, select=True,
        help='The internal or programmatical name of the role.')


class WebUser:
    __metaclass__ = PoolMeta
    __name__ = 'web.user'
    _history = True
    _rec_name = 'email'
    nickname = fields.Char(
        'Nickname', help='The name shown to other users')
    user = fields.One2One(
        'web.user-res.user', 'web_user', 'res_user', 'Tryton User',
        readonly=True, states={'required': Greater(Eval('active_id', -1), 0)},
        help='The Tryton user of the web user')
    party = fields.One2One(
        'web.user-party.party', 'user', 'party', 'Party',
        states={'required': Greater(Eval('active_id', -1), 0)},
        help='The party of the web user')
    clients = fields.One2Many('client', 'web_user', 'Clients')
    roles = fields.Many2Many(
        'web.user-web.user.role', 'user', 'role', 'Roles')
    default_role = fields.Selection('get_roles', 'Default Role')
    acl = fields.One2Many(
        'ace', 'web_user', 'Access Control List',
        help="The permissions for a web user.")
    picture_data = fields.Binary(
        'Picture Data', help='Picture Data')
    picture_data_mime_type = fields.Char(
        'Picture Data Mime Type', help='The mime type of picture data.')
    opt_in_state = fields.Selection(
        _OPT_IN_STATES, 'Opt-in State',
        help='The authentication state of the opt-in method:\n\n'
        'New: The web-user is newly created.\n'
        'Mail Sent: An opt-in link is sent to the email.\n'
        'Opted-In: The link is clicked.\n'
        'Opted-Out: The web-user opted-out.')
    opt_in_uuid = fields.Char(
        'Opt-in UUID',
        help='The universally unique identifier of the opt-in of a web user')
    opt_in_timestamp = fields.DateTime('Date of Opt-in')
    opt_out_timestamp = fields.DateTime('Date of Opt-out')
    abuse_rank = fields.Integer(
        'Abuse Rank', help='Times of potential abuse.')
    new_email = fields.Char(
        'New Email', help='On profile change, the new email '
        'stays here till the user clicks the activation link')

    @classmethod
    def __setup__(cls):
        super(WebUser, cls).__setup__()
        cls.__rpc__.update(
            {'authenticate': RPC(check_access=False)})
        cls._sql_constraints += [
            ('opt_in_uuid_uniq', 'UNIQUE(opt_in_uuid)',
                'The opt-in UUID of the Webuser must be unique.'),
        ]

    @staticmethod
    def default_opt_in_state():
        return 'new'

    @staticmethod
    def default_opt_in_uuid():
        return str(uuid.uuid4())

    @staticmethod
    def get_roles():
        Role = Pool().get('web.user.role')
        roles = Role.search([])
        return [(x.code, x.name) for x in roles] + [(None, '')]

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        User = pool.get('res.user')
        Party = pool.get('party.party')
        Artist = pool.get('artist')
        WebUserRole = pool.get('web.user.role')
        licenser = WebUserRole.search([('code', '=', 'licenser')])
        if licenser:
            licenser = licenser[0]

        vlist = [x.copy() for x in vlist]
        for values in vlist:
            nickname = values.get('nickname')
            email = values.get('email')
            user_email = email + ':::' + ''.join(
                random.sample(string.lowercase, 10))

            # autocreate party
            if not values.get('party'):
                values['party'] = Party.create(
                    [
                        {
                            'name': nickname or email,
                            'contact_mechanisms': [(
                                'create', [{
                                    'type': 'email',
                                    'value': email
                                }]
                            )]
                        }])[0].id

            # autocreate user
            if not values.get('user'):
                values['user'] = User.create(
                    [
                        {
                            'name': nickname or user_email,
                            'login': user_email,
                            'email': email,
                            'active': False,
                        }])[0].id

        elist = super(WebUser, cls).create(vlist)
        for entry in elist:
            # autocreate first artist
            if licenser in entry.roles and entry.nickname:
                artist, = Artist.create(
                    [

                        {
                            'name': nickname,
                            'party': entry.party.id,
                            'entity_origin': 'direct',
                            'entity_creator': entry.party.id,
                            'claim_state': 'claimed'
                        }])
                entry.party.artists = [artist]
                entry.party.default_solo_artist = artist.id
                entry.party.save()

        return elist


class WebUserResUser(ModelSQL):
    'Web User - Tryton User'
    __name__ = 'web.user-res.user'
    web_user = fields.Many2One(
        'web.user', 'Web User', ondelete='CASCADE', select=True, required=True)
    res_user = fields.Many2One(
        'res.user', 'Tryton User', ondelete='CASCADE', select=True,
        required=True)

    @classmethod
    def __setup__(cls):
        super(WebUserResUser, cls).__setup__()
        cls._sql_constraints += [
            ('web_user_uniq', 'UNIQUE("web_user")',
                'Error!\n'
                'A web user can only be linked to one Tryton user.\n'
                'The used web user is already linked to another Tryton user.'),
            ('res_user_uniq', 'UNIQUE("res_user")',
                'Error!\n'
                'A Tryton user can only be linked to one web user.\n'
                'The used Tryton user is already linked to another web user.'),
        ]


class WebUserWebUserRole(ModelSQL, ModelView):
    "Web User - Web User Role"
    __name__ = 'web.user-web.user.role'
    _history = True

    user = fields.Many2One(
        'web.user', 'User', ondelete='CASCADE', select=True, required=True)
    role = fields.Many2One(
        'web.user.role', 'Role', ondelete='CASCADE', select=True,
        required=True)


class WebUserParty:
    __metaclass__ = PoolMeta
    __name__ = 'web.user-party.party'
    _history = True

    @classmethod
    def __setup__(cls):
        super(WebUserParty, cls).__setup__()
        cls._sql_constraints += [
            ('user_uniq', 'UNIQUE("user")',
                'Error!\n'
                'A web user can only be linked to one party.\n'
                'The used web user is already linked to another party.'),
            ('party_uniq', 'UNIQUE(party)',
                'Error!\n'
                'A party can only be linked to one web user.\n'
                'The used party is already linked to another web user.'),
        ]
