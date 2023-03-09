# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society
from trytond.pool import PoolMeta
from trytond.model import fields

__all__ = ['Invoice', 'InvoiceLine']


class Invoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    allocation = fields.One2One(
        'allocation-account.invoice', 'invoice', 'allocation',
        'Invoice Allocation',
        help='The allocation of the invoice')

    # TODO: set allocation.state = 'collected', when invoice is payed
    # optimal: in atomic transaction context, so rollbacks roll back both


class InvoiceLine(metaclass=PoolMeta):
    __name__ = 'account.invoice.line'

    @classmethod
    def _get_origin(cls):
        models = super(InvoiceLine, cls)._get_origin()
        # TODO: maybe allocation?
        models.append('utilisation')
        return models
