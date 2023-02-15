# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society
from trytond.pool import PoolMeta

__all__ = ['InvoiceLine']


class InvoiceLine(metaclass=PoolMeta):
    __name__ = 'account.invoice.line'

    @classmethod
    def _get_origin(cls):
        models = super(InvoiceLine, cls)._get_origin()
        models.append('utilisation')
        return models
