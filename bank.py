# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta


__all__ = [
    'BankAccount',
]
__metaclass__ = PoolMeta


class BankAccount():
    __name__ = 'bank.account'
    owner = fields.One2One(
        'bank.account-party.party', 'account', 'owner', 'Owner')
