# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society
from trytond.pool import PoolMeta, Pool
from trytond.model import fields, Workflow

__all__ = ['Invoice', 'InvoiceLine']


class Invoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    allocation = fields.One2One(
        'allocation-account.invoice', 'invoice', 'allocation',
        'Invoice Allocation',
        help='The allocation of the invoice')
    distribution = fields.Many2One(
        'distribution', 'Distribution',
        help='The allocation of the invoice')

    @classmethod
    @Workflow.transition('paid')
    def paid(cls, invoices):
        # TODO: atomic transaction context
        super(Invoice, cls).paid(invoices)
        for invoice in invoices:
            # licenser invoice
            if not invoice.allocation:
                continue
            # licensee invoice
            invoice.allocation.state = 'collected'
            invoice.allocation.save()
            # finish declarations
            for utilisation in invoice.allocation.utilisations:
                declaration = utilisation.declaration
                if declaration.period == 'onetime':
                    declaration.state = 'finished'
                    declaration.save()


class InvoiceLine(metaclass=PoolMeta):
    __name__ = 'account.invoice.line'

    @classmethod
    def _get_origin(cls):
        models = super(InvoiceLine, cls)._get_origin()
        models += ['utilisation', 'distribution']
        return models
