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
__metaclass__ = PoolMeta
_OPT_IN_STATES = [
    ('new', 'New'),
    ('mail-sent', 'Mail Sent'),
    ('opted-in', 'Opted-In'),
    ('opted-out', 'Opted-Out'),
]


class WebUserRole(ModelSQL, ModelView):
    "Web User Role"
    __name__ = 'web.user.role'

    name = fields.Char(
        'Name', required=True, select=True, translate=True,
        help='The display name of role.')
    code = fields.Char(
        'Code', required=True, select=True,
        help='The internal or programmatical name of the role.')


class WebUser:
    __name__ = 'web.user'
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
    pocket_account = fields.Many2One(
        'account.account', 'Account')
    clients = fields.One2Many('client', 'web_user', 'Clients')
    roles = fields.Many2Many(
        'web.user-web.user.role', 'user', 'role', 'Roles')
    default_role = fields.Selection('get_roles', 'Default Role')
    show_creative_info = fields.Boolean(
        'Show Creative Info', help='Check, if the infobox is shown')
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
    def default_show_creative_info():
        return True

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

        vlist = [x.copy() for x in vlist]
        for values in vlist:
            email = values.get('email')
            user_email = email + ':::' + ''.join(
                random.sample(string.lowercase, 10))
            if not values.get('party'):
                values['party'] = Party.create(
                    [{'name': email}])[0].id
            if not values.get('user'):
                values['user'] = User.create(
                    [
                        {
                            'name': user_email,
                            'login': user_email,
                            'email': email,
                            'active': False,
                        }])[0].id

        return super(WebUser, cls).create(vlist)

    @classmethod
    def get_balance(cls, items, names):
        '''
        Function to compute hat balance for artist
        or pocket balance party items.
        '''
        res = {}
        pool = Pool()
        MoveLine = pool.get('account.move.line')
        Account = pool.get('account.account')
        User = pool.get('res.user')
        cursor = Transaction().cursor

        line = MoveLine.__table__()
        account = Account.__table__()

        for name in names:
            if name not in ('hat_balance', 'pocket_balance'):
                raise Exception('Bad argument')
            res[name] = dict((i.id, Decimal('0.0')) for i in items)

        user_id = Transaction().user
        if user_id == 0 and 'user' in Transaction().context:
            user_id = Transaction().context['user']
        user = User(user_id)
        if not user.company:
            return res
        company_id = user.company.id

        with Transaction().set_context(posted=False):
            line_query, _ = MoveLine.query_get(line)
        clause = ()
        if name == 'hat_balance':
            field = line.artist
            clause = line.artist.in_([i.id for i in items])
        if name == 'pocket_balance':
            field = line.party
            clause = line.party.in_([i.id for i in items])
        for name in names:
            query = line.join(
                account, condition=account.id == line.account).select(
                    field,
                    Sum(Coalesce(line.debit, 0) - Coalesce(line.credit, 0)),
                    where=account.active
                    & (account.kind == name[:-8])
                    & clause
                    & (line.reconciliation == None)
                    & (account.company == company_id)
                    & line_query,
                    group_by=field)
            cursor.execute(*query)
            for id_, sum in cursor.fetchall():
                # SQLite uses float for SUM
                if not isinstance(sum, Decimal):
                    sum = Decimal(str(sum))
                res[name][id_] = - sum
        return res

    @classmethod
    def search_balance(cls, name, clause):
        pool = Pool()
        MoveLine = pool.get('account.move.line')
        Account = pool.get('account.account')
        Company = pool.get('company.company')
        User = pool.get('res.user')

        line = MoveLine.__table__()
        account = Account.__table__()

        if name not in ('hat_balance', 'pocket_balance'):
            raise Exception('Bad argument')

        company_id = None
        user_id = Transaction().user
        if user_id == 0 and 'user' in Transaction().context:
            user_id = Transaction().context['user']
        user = User(user_id)
        if Transaction().context.get('company'):
            child_companies = Company.search(
                [
                    ('parent', 'child_of', [user.main_company.id]),
                ])
            if Transaction().context['company'] in child_companies:
                company_id = Transaction().context['company']

        if not company_id:
            if user.company:
                company_id = user.company.id
            elif user.main_company:
                company_id = user.main_company.id

        if not company_id:
            return []

        line_query, _ = MoveLine.query_get(line)
        Operator = fields.SQL_OPERATORS[clause[1]]
        if name == 'hat_balance':
            field = line.artist
            where_clause = (line.artist != None)
            sign = -1
        if name == 'pocket_balance':
            field = line.party
            where_clause = (line.party != None)
            sign = 1
        query = line.join(
            account, condition=account.id == line.account).select(
                field,
                where=account.active
                & (account.kind == 'hat')
                & where_clause
                & (line.reconciliation == None)
                & (account.company == company_id)
                & line_query,
                group_by=field,
                having=Operator(
                    Mul(
                        sign, Sum(
                            Coalesce(line.debit, 0)
                            - Coalesce(line.credit, 0))),
                    Decimal(clause[2] or 0)))
        return [('id', 'in', query)]


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
            ('party_uniq', 'UNIQUE("res_user")',
                'Error!\n'
                'A Tryton user can only be linked to one web user.\n'
                'The used Tryton user is already linked to another web user.'),
        ]


class WebUserWebUserRole(ModelSQL, ModelView):
    "Web User - Web User Role"
    __name__ = 'web.user-web.user.role'

    user = fields.Many2One(
        'web.user', 'User', ondelete='CASCADE', select=True, required=True)
    role = fields.Many2One(
        'web.user.role', 'Role', ondelete='CASCADE', select=True,
        required=True)


class WebUserParty:
    __name__ = 'web.user-party.party'

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
