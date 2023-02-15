# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society
from trytond.model import fields
from trytond.pool import PoolMeta


__all__ = [
    'BankAccount',
    'BankAccountNumber',
]


class BankAccount(metaclass=PoolMeta):
    __name__ = 'bank.account'
    _history = True
    owner = fields.One2One(
        'bank.account-party.party', 'account', 'owner', 'Owner')


class BankAccountNumber(metaclass=PoolMeta):
    __name__ = 'bank.account.number'
    _history = True
