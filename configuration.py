# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society
from trytond.model import ModelView, ModelSQL, ModelSingleton, fields
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.pyson import Eval


__all__ = ['Configuration']


class Configuration(ModelSingleton, ModelSQL, ModelView):
    'Configuration'
    __name__ = 'collecting_society.configuration'

    artist_sequence = fields.Property(
        fields.Many2One('ir.sequence', 'Artist Sequence', domain=[
            ('code', '=', 'artist'),
        ]))
    contribution_sequence = fields.Property(
        fields.Many2One('ir.sequence', 'Contribution Sequence', domain=[
            ('code', '=', 'contribution'),
        ]))
    creation_sequence = fields.Property(
        fields.Many2One('ir.sequence', 'Creation Sequence', domain=[
            ('code', '=', 'creation'),
        ]))
    utilisation_sequence = fields.Property(fields.Many2One(
        'ir.sequence', 'Utilisation Sequence', domain=[
            ('code', '=', 'creation.utilisation'),
        ]))
    distribution_sequence = fields.Property(
        fields.Many2One('ir.sequence', 'Distribution Sequence', domain=[
            ('code', '=', 'distribution'),
        ]))
    default_hat_account = fields.Function(
        fields.Many2One(
            'account.account', 'Default Hat Account',
            domain=[
                ('kind', '=', 'hat'),
                ('company', '=', Eval('context', {}).get('company', -1)),
            ]), 'get_account', setter='set_account')
    default_pocket_account = fields.Function(
        fields.Many2One(
            'account.account', 'Default Pocket Account',
            domain=[
                ('kind', '=', 'pocket'),
                ('company', '=', Eval('context', {}).get('company', -1)),
            ]), 'get_account', setter='set_account')

    def get_account(self, name):
        pool = Pool()
        Property = pool.get('ir.property')
        ModelField = pool.get('ir.model.field')
        company_id = Transaction().context.get('company')
        model = 'party.party'
        if name == 'default_hat_account':
            model = 'artist'
        account_field = ModelField.search(
            [
                ('model.model', '=', model),
                ('name', '=', name[8:]),
            ], limit=1)
        if not account_field:
            return None
        account_field = account_field[0]
        properties = Property.search(
            [
                ('field', '=', account_field.id),
                ('res', '=', None),
                ('company', '=', company_id),
            ], limit=1)
        if properties:
            prop, = properties
            return prop.value.id

    @classmethod
    def set_account(cls, configurations, name, value):
        pool = Pool()
        Property = pool.get('ir.property')
        ModelField = pool.get('ir.model.field')
        company_id = Transaction().context.get('company')
        model = 'party.party'
        if name == 'default_hat_account':
            model = 'artist'
        account_field, = ModelField.search(
            [
                ('model.model', '=', model),
                ('name', '=', name[8:]),
            ], limit=1)
        properties = Property.search(
            [
                ('field', '=', account_field.id),
                ('res', '=', None),
                ('company', '=', company_id),
            ])
        Property.delete(properties)
        if value:
            Property.create(
                [
                    {
                        'field': account_field.id,
                        'value': 'account.account,%s' % value,
                        'company': company_id,
                    }])
