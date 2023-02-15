# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society
from trytond.model import ModelView, ModelSQL, ModelSingleton, fields
from trytond.model import MultiValueMixin
from trytond.pool import Pool
from trytond.pyson import Id


__all__ = ['Configuration']

artist_sequence = fields.Many2One(
    'ir.sequence', 'Artist Sequence', domain=[
        ('sequence_type', '=',
            Id('collecting_society', 'sequence_type_artist')),
        ])
release_sequence = fields.Many2One(
    'ir.sequence', 'Release Sequence', domain=[
        ('sequence_type', '=',
            Id('collecting_society', 'sequence_type_release')),
        ])
creation_sequence = fields.Many2One(
    'ir.sequence', 'Creation Sequence', domain=[
        ('sequence_type', '=',
            Id('collecting_society', 'sequence_type_creation')),
        ])
content_sequence = fields.Many2One(
    'ir.sequence', 'Content Sequence', domain=[
        ('sequence_type', '=',
            Id('collecting_society', 'sequence_type_content')),
        ])
tariff_system_sequence = fields.Many2One(
    'ir.sequence', 'Tariff System Sequence', domain=[
        ('sequence_type', '=',
            Id('collecting_society', 'sequence_type_tariff_system')),
        ])
declaration_sequence = fields.Many2One(
    'ir.sequence', 'Declaration Sequence', domain=[
        ('sequence_type', '=',
            Id('collecting_society', 'sequence_type_declaration')),
        ])
utilisation_sequence = fields.Many2One(
    'ir.sequence', 'Utilisation Sequence', domain=[
        ('sequence_type', '=',
            Id('collecting_society', 'sequence_type_utilisation')),
        ])
distribution_sequence = fields.Many2One(
    'ir.sequence', 'Distribution Sequence', domain=[
        ('sequence_type', '=',
            Id('collecting_society', 'sequence_type_distribution')),
        ])
distribution_plan_sequence = fields.Many2One(
    'ir.sequence', 'Distribution Plan Sequence', domain=[
        ('sequence_type', '=',
            Id('collecting_society', 'sequence_type_distribution_plan')),
        ])
harddisk_label_sequence = fields.Many2One(
    'ir.sequence', 'Harddisk Label Sequence', domain=[
        ('sequence_type', '=',
            Id('collecting_society', 'sequence_type_harddisk_label')),
        ])
filesystem_label_sequence = fields.Many2One(
    'ir.sequence', 'Filesystem Label Sequence', domain=[
        ('sequence_type', '=',
            Id('collecting_society', 'sequence_type_filesystem_label')),
        ])


class Configuration(ModelSingleton, ModelSQL, ModelView, MultiValueMixin):
    'Collecting Society Configuration'
    __name__ = 'collecting_society.configuration'

    artist_sequence = fields.MultiValue(artist_sequence)
    release_sequence = fields.MultiValue(release_sequence)
    creation_sequence = fields.MultiValue(creation_sequence)
    content_sequence = fields.MultiValue(content_sequence)
    tariff_system_sequence = fields.MultiValue(tariff_system_sequence)
    declaration_sequence = fields.MultiValue(declaration_sequence)
    utilisation_sequence = fields.MultiValue(utilisation_sequence)
    distribution_sequence = fields.MultiValue(distribution_sequence)
    distribution_plan_sequence = fields.MultiValue(distribution_plan_sequence)
    harddisk_label_sequence = fields.MultiValue(harddisk_label_sequence)
    filesystem_label_sequence = fields.MultiValue(filesystem_label_sequence)

    @classmethod
    def default_artist_sequence(cls, **pattern):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id('collecting_society', 'sequence_artist')
        except KeyError:
            return None

    @classmethod
    def default_release_sequence(cls, **pattern):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id('collecting_society', 'sequence_release')
        except KeyError:
            return None

    @classmethod
    def default_creation_sequence(cls, **pattern):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id('collecting_society', 'sequence_creation')
        except KeyError:
            return None

    @classmethod
    def default_content_sequence(cls, **pattern):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id('collecting_society', 'sequence_content')
        except KeyError:
            return None

    @classmethod
    def default_tariff_system_sequence(cls, **pattern):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id(
                'collecting_society', 'sequence_tariff_system')
        except KeyError:
            return None

    @classmethod
    def default_declaration_sequence(cls, **pattern):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id(
                'collecting_society', 'sequence_declaration')
        except KeyError:
            return None

    @classmethod
    def default_utilisation_sequence(cls, **pattern):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id(
                'collecting_society', 'sequence_utilisation')
        except KeyError:
            return None

    @classmethod
    def default_distribution_sequence(cls, **pattern):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id(
                'collecting_society', 'sequence_distribution')
        except KeyError:
            return None

    @classmethod
    def default_distribution_plan_sequence(cls, **pattern):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id(
                'collecting_society', 'sequence_distribution_plan')
        except KeyError:
            return None

    @classmethod
    def default_harddisk_label_sequence(cls, **pattern):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id(
                'collecting_society', 'sequence_harddisk_label')
        except KeyError:
            return None

    @classmethod
    def default_filesystem_label_sequence(cls, **pattern):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id(
                'collecting_society', 'sequence_filesystem_label')
        except KeyError:
            return None

# class ConfigurationSequence(ModelSQL, ValueMixin):
#     'Party Configuration Sequence'
#     __name__ = 'party.configuration.party_sequence'
#     party_sequence = party_sequence
#     _configuration_value_field = 'party_sequence'
#
#     @classmethod
#     def check_xml_record(cls, records, values):
#         return True
