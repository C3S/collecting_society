# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Bool
from trytond.transaction import Transaction


__all__ = [
    'Party',
]
__metaclass__ = PoolMeta


class Party:
    __name__ = 'party.party'

    artists = fields.One2Many('artist', 'party', 'Artists')
    default_solo_artist = fields.Many2One(
        'artist', 'Default Solo Artist',
        help='The default solo artist of this party')
    currency_digits = fields.Function(
        fields.Integer('Currency Digits'), 'get_currency_digits')
    pocket_balance = fields.Function(
        fields.Numeric(
            'Pocket Balance', digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_pocket_balance', searcher='search_pocket_balance')
    pocket_budget = fields.Numeric(
        'Budget', digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits'])
    pocket_account = fields.Property(
        fields.Many2One(
            'account.account', 'Pocket Account', domain=[
                ('kind', '=', 'pocket'),
                ('company', '=', Eval('context', {}).get('company', -1)),
            ], states={
                'required': Bool(Eval('context', {}).get('company')),
                'invisible': ~Eval('context', {}).get('company'),
            }))

    def get_currency_digits(self, name):
        Company = Pool().get('company.company')
        if Transaction().context.get('company'):
            company = Company(Transaction().context['company'])
            return company.currency.digits
        return 2

    @classmethod
    def get_pocket_balance(cls, artists, names):
        WebUser = Pool().get('web.user')

        result = WebUser.get_balance(items=artists, names=names)
        return result

    @classmethod
    def search_pocket_balance(cls, name, clause):
        WebUser = Pool().get('web.user')

        result = WebUser.search_balance(name, clause)
        return result

    @staticmethod
    def default_pocket_budget():
        return Decimal('0')
