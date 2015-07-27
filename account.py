# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society
from trytond.model import fields
from trytond.pool import PoolMeta


__all__ = ['AccountTemplate', 'Account', 'AccountMove', 'AccountMoveLine']
__metaclass__ = PoolMeta


class AccountTemplate:
    __name__ = 'account.account.template'

    @classmethod
    def __setup__(cls):
        super(AccountTemplate, cls).__setup__()
        cls.kind.selection += [('hat', 'Hat'), ('pocket', 'Pocket')]


class Account:
    __name__ = 'account.account'

    @classmethod
    def __setup__(cls):
        super(Account, cls).__setup__()
        cls.kind.selection += [('hat', 'Hat'), ('pocket', 'Pocket')]


class AccountMove():
    __name__ = 'account.move'

    @classmethod
    def _get_origin(cls):
        return (
            super(AccountMove, cls)._get_origin()
            + ['distribution.allocation'])


class AccountMoveLine():
    __name__ = 'account.move.line'

    artist = fields.Many2One('artist', 'Artist', select=True)

    @classmethod
    def __setup__(cls):
        super(AccountMoveLine, cls).__setup__()
        if 'invisible' in cls.party.states:
            cls.party.states['invisible'] = False

    # Cannot use super here as we need to remove only one check
    # of this method from module account
    def check_account(self):
        if self.account.kind in ('view',):
            self.raise_user_error(
                'move_view_account', (self.account.rec_name,))
        if not self.account.active:
            self.raise_user_error(
                'move_inactive_account', (self.account.rec_name,))
