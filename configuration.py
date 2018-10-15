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
    release_sequence = fields.Property(
        fields.Many2One('ir.sequence', 'Release Sequence', domain=[
            ('code', '=', 'release'),
        ]))
    creation_sequence = fields.Property(
        fields.Many2One('ir.sequence', 'Creation Sequence', domain=[
            ('code', '=', 'creation'),
        ]))
    content_sequence = fields.Property(
        fields.Many2One('ir.sequence', 'Content Sequence', domain=[
            ('code', '=', 'content'),
        ]))

    tariff_system_sequence = fields.Property(
        fields.Many2One('ir.sequence', 'Tariff System Sequence', domain=[
            ('code', '=', 'tariff_system'),
        ]))

    harddisk_label_sequence = fields.Property(
        fields.Many2One('ir.sequence', 'Harddisk Label Sequence', domain=[
            ('code', '=', 'harddisk.label'),
        ]))
    filesystem_label_sequence = fields.Property(
        fields.Many2One('ir.sequence', 'Filesystem Label Sequence', domain=[
            ('code', '=', 'harddisk.filesystem.label'),
        ]))
    utilisation_sequence = fields.Property(
        fields.Many2One('ir.sequence', 'Utilisation Sequence', domain=[
            ('code', '=', 'creation.utilisation'),
        ]))
    distribution_sequence = fields.Property(
        fields.Many2One('ir.sequence', 'Distribution Sequence', domain=[
            ('code', '=', 'distribution'),
        ]))
