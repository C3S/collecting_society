# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society
from trytond.pool import PoolMeta

__all__ = [
    'AccountMove',
]


class AccountMove(metaclass=PoolMeta):
    __name__ = 'account.move'

    @classmethod
    def _get_origin(cls):
        return (
            super(AccountMove, cls)._get_origin()
            + ['allocation', 'distribution'])
