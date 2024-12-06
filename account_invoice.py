# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society
from trytond.pool import PoolMeta
from trytond.model import fields, Workflow

__all__ = ['Invoice', 'InvoiceLine']


class Invoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    allocation = fields.One2One(
        'allocation-account.invoice', 'invoice', 'allocation',
        'Invoice Allocation',
        help='The allocation of the invoice')

    @classmethod
    @Workflow.transition('paid')
    def paid(cls, invoices):
        # TODO: atomic transaction context
        super(Invoice, cls).paid(invoices)
        for invoice in invoices:
            if not invoice.allocation:
                continue
            invoice.allocation.state = 'collected'
            invoice.allocation.save()


class InvoiceLine(metaclass=PoolMeta):
    __name__ = 'account.invoice.line'

    @classmethod
    def _get_origin(cls):
        models = super(InvoiceLine, cls)._get_origin()
        models.append('utilisation')
        return models
