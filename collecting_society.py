# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society
import sys
import os
import uuid
import datetime
import requests
import json
import copy
import math
from decimal import Decimal
from typing import Protocol, Any
from sql import Table
from sql.conditionals import Case
from sql.functions import CharLength
import hurry.filesize

from trytond.model import Model, ModelView, ModelSQL, fields, Unique
from trytond.model.model import ModelMeta
from trytond.model.fields import Field
from trytond.wizard import Wizard, StateView, Button, StateTransition,  \
    StateAction
from trytond.exceptions import UserError, UserWarning

from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.pyson import Eval, Bool, Or, And

from .formulas import utils, collection, distribution


__all__ = [

    # Mixins
    'UUID',
    'Code',
    'CodeSequence',
    'PublicApi',
    'CurrentState',
    'ClaimState',
    'CommitState',
    'EntityOrigin',
    'CurrencyDigits',
    'AccessControlList',
    'MixinRight',
    'MixinIdentifier',
    'MixinIdentifierHelper',

    # Collecting Society
    'CollectingSociety',
    'TariffSystem',
    'TariffCategory',
    'TariffAdjustmentCategory',
    'TariffCategoryTariffAdjustmentCategory',
    'TariffAdjustment',
    'TariffRelevanceCategory',
    'TariffCategoryTariffRelevanceCategory',
    'TariffRelevance',
    'Tariff',
    'Allocation',
    'AllocationAccountInvoice',
    'CollectStart',
    'Collect',
    'AllocationInvoice',
    'Collection',
    'Distribution',
    'DistributionAccountMove',
    'DistributionPlan',
    'DistributeStart',
    'Distribute',
    'EventIndicators',
    'LocationIndicators',
    'LocationIndicatorsPeriod',
    'LocationSpaceIndicators',
    'WebsiteResourceIndicators',
    'ReleaseIndicators',
    'UtilisationIndicators',
    'IndicatorsMeta',

    # Licenser
    'License',
    'Artist',
    'ArtistArtist',
    'ArtistRelease',
    'ArtistPayeeAcceptance',
    'ArtistIdentifier',
    'ArtistIdentifierSpace',
    'ArtistPlaylist',
    'ArtistPlaylistItem',
    'Creation',
    'CreationDerivative',
    'CreationRole',
    'CreationTariffCategory',
    'CreationIdentifier',
    'CreationIdentifierSpace',
    'CreationRight',
    'CreationRightCreationRight',
    'Release',
    'ReleaseTrack',
    'ReleaseGenre',
    'ReleaseStyle',
    'ReleaseIdentifier',
    'ReleaseIdentifierSpace',
    'ReleaseRight',
    'ReleaseRightReleaseRight',
    'MixinIdentifier',
    'Instrument',
    'CreationRightInstrument',
    'Genre',
    'Style',
    'Label',
    'Publisher',

    # Licensee
    'Event',
    'EventPerformance',
    'Location',
    'LocationCategory',
    'LocationSpace',
    'LocationSpaceCategory',
    'Website',
    'WebsiteCategory',
    'WebsiteResource',
    'WebsiteResourceCreation',
    'WebsiteResourceCategory',
    'WebsiteCategoryWebsiteResourceCategory',
    'Device',
    'DeviceMessage',
    'DeviceMessageDeviceMessage',
    'DeviceAssignment',
    'DeviceMessageFingerprint',
    'DeviceMessageFingerprintMatch',
    'DeviceMessageFingerprintMatchStart',
    'DeviceMessageFingerprintMerge',
    'DeviceMessageFingerprintMergeStart',
    'DeviceMessageFingerprintMergeSelect',
    'DeviceMessageFingerprintCreationlist',
    'DeviceMessageFingerprintCreationlistItem',
    'DeviceMessageUsagereport',
    'Declaration',
    'DeclarationGroup',
    'Utilisation',
    'UtilisationCalculate',
    'UtilisationConfirm',
    'UtilisationFinalize',
    'UtilisationCreationlist',
    'UtilisationCreationlistItem',

    # Archiving
    'Storehouse',
    'HarddiskLabel',
    'Harddisk',
    'HarddiskTest',
    'FilesystemLabel',
    'Filesystem',
    'Content',
    'Checksum',
    'Fingerprintlog',

    # Portal
    'AccessControlEntry',
    'AccessControlEntryRole',
    'AccessRole',
    'AccessRolePermission',
    'AccessPermission',

    # Tryton
    'STATES',
    'DEPENDS',

]
STATES = {
    'readonly': ~Eval('active'),
}
DEPENDS = ['active']
SEPARATOR = ' /25B6 '
DEFAULT_ACCESS_ROLES = ['Administrator', 'Stakeholder']


##############################################################################
# Mixins
##############################################################################


class UUID:
    'Mixin to add a machine readable uuid field for internal use'
    __slots__ = ()

    uuid = fields.Char(
        'UUID', required=True,
        help='The machine readable UUID for the record for internal use.')

    @classmethod
    def __setup__(cls):
        super().__setup__()
        table = cls.__table__()
        cls._sql_constraints += [
            ('uuid_uniq', Unique(table, table.uuid),
             f'The UUID of the {cls.__name__} must be unique.'),
        ]

    @staticmethod
    def default_uuid():
        return str(uuid.uuid4())

    @classmethod
    def create(cls, vlist):
        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if not values.get('code'):
                values['uuid'] = cls.default_uuid()
        return super().create(vlist)

    @classmethod
    def copy(cls, vlist, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['uuid'] = None
        return super().copy(vlist, default=default)

    @classmethod
    def search_rec_name(cls, name, clause):
        return [('uuid',) + tuple(clause[1:])]


class PublicApiProtocol(Protocol):
    def __setup__(self) -> None: ...
    def __table__(self) -> Table: ...
    _sql_constraints: list[tuple[str, Any, str]]


class Code:
    'Mixin to add a free code field for technical use and public reference'
    __slots__ = ()

    code = fields.Char(
        'Code', required=True,
        help='The code for technical use and public reference.')

    @classmethod
    def __setup__(cls):
        super().__setup__()
        table = cls.__table__()
        cls._sql_constraints += [
            ('code_uniq', Unique(table, table.code),
             f'The code of the {cls.__name__} must be unique.'),
        ]

    @staticmethod
    def order_code(tables):
        table, _ = tables[None]
        return [CharLength(table.code), table.code]

    @classmethod
    def copy(cls, vlist, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['code'] = None
        return super().copy(vlist, default=default)

    @classmethod
    def search_rec_name(cls, name, clause):
        return [('code',) + tuple(clause[1:])]


class CodeSequence:
    'Mixin to add a human readable sequence code field for public reference'
    __slots__ = ()

    # name of sequence field in collecting_society.configuration
    _code_sequence = ''

    code = fields.Char(
        'Code', required=True, states={
            'readonly': True,
        }, help="The official public sequence code of the "
                f"{_code_sequence.replace('_', ' ')}")

    @classmethod
    def __setup__(cls):
        super().__setup__()
        table = cls.__table__()
        cls._sql_constraints = [
            ('code_uniq', Unique(table, table.code),
             f"The code of the {cls._code_sequence.replace('_', ' ')} "
             "must be unique."),
        ]

    @staticmethod
    def order_code(tables):
        table, _ = tables[None]
        return [CharLength(table.code), table.code]

    @classmethod
    def create(cls, vlist):
        Configuration = Pool().get('collecting_society.configuration')
        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if not values.get('code'):
                config = Configuration(1)
                sequence = getattr(config, cls._code_sequence)
                values['code'] = sequence.get()
        return super().create(vlist)

    @classmethod
    def copy(cls, vlist, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['code'] = None
        return super().copy(vlist, default=default)

    @classmethod
    def search_rec_name(cls, name, clause):
        return [('code',) + tuple(clause[1:])]


class PublicApi:
    'Mixin to add a machine readable oid field for public use'
    __slots__ = ()

    oid = fields.Char(
        'OID', required=True,
        help='A unique object identifier used in the public web api to avoid'
             'exposure of implementation details to the users.')

    @classmethod
    def __setup__(cls: PublicApiProtocol):
        super().__setup__()
        table = cls.__table__()
        cls._sql_constraints += [
            ('oid_uniq', Unique(table, table.oid),
             f'The OID of the {cls.__name__} must be unique.'),
        ]

    @staticmethod
    def default_oid():
        return str(uuid.uuid4())

    @classmethod
    def create(cls, vlist):
        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if not values.get('code'):
                values['oid'] = cls.default_oid()
        return super().create(vlist)

    @classmethod
    def copy(cls, vlist, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['oid'] = None
        return super().copy(vlist, default=default)

    @classmethod
    def search_rec_name(cls, name, clause):
        return [('oid',) + tuple(clause[1:])]


class CurrentState:
    'Mixin for the active state'
    __slots__ = ()
    active = fields.Boolean('Active')

    @staticmethod
    def default_active():
        return True


class ClaimState:
    'Mixin for the claim workflow'
    __slots__ = ()
    claim_state = fields.Selection(
        [
            ('unclaimed', 'Unclaimed'),
            ('claimed', 'Claimed'),
            ('revised', 'Revised'),
        ], 'Claim', states={'required': True}, sort=False,
        help='The state in a claim process.\n\n'
        '*Unclaimed*: Object is not yet claimed or a claim was cancelled.\n'
        '*Claimed*: Someone claimed this object but it was not revised yet.\n'
        '*Revised*: The claim was confirmed by administration')

    @staticmethod
    def default_claim_state():
        return "unclaimed"


class CommitState:
    'Mixin for the commit workflow'
    __slots__ = ()
    commit_state = fields.Selection(
        [
            ('uncommited', 'Uncommited'),
            ('commited', 'Commited'),
            ('revised', 'Revised'),
            ('rejected', 'Rejected'),
            ('deleted', 'Deleted'),
        ], 'Commit', states={'required': True}, sort=False,
        help='The state in a commit process.\n\n'
        '*Uncommited*: The object was freshly created.\n'
        '*Commited*: The object was commited by the web user.\n'
        '*Revised*: The commit was revised by administration.\n'
        '*Rejected*: The commit was rejected by administration.\n'
        '*Deleted*: The rejeted object was deleted.\n')

    @staticmethod
    def default_commit_state():
        return 'uncommited'


class CurrencyDigits:
    'Mixin to provide the currency digit configuration'
    __slots__ = ()
    currency_digits = fields.Function(
        fields.Integer('Currency Digits'), 'get_currency_digits')

    def get_currency_digits(self, name):
        Company = Pool().get('company.company')
        if Transaction().context.get('company'):
            company = Company(Transaction().context['company'])
            return company.currency.digits
        return 2


class AccessControlList:
    'Mixin to add an Access Control List'
    __slots__ = ()
    acl = fields.One2Many(
        'ace', 'entity', 'Access Control List',
        states=STATES, depends=DEPENDS,
        help='A list of acces control entries with object permissions.')

    def permits(self, web_user, code, derive=True):
        for ace in self.acl:
            if ace.web_user != web_user:
                continue
            for role in ace.roles:
                for permission in role.permissions:
                    if permission.code == code:
                        return True
        return False

    def permissions(self, web_user, valid_codes=[], derive=True):
        permissions = set()
        for ace in self.acl:
            if ace.web_user != web_user:
                continue
            permissions.update([
                permission.code
                for role in ace.roles
                for permission in role.permissions])
        if valid_codes:
            permissions = permissions.intersection(valid_codes)
        return tuple(permissions)


class EntityOrigin:
    'Mixin to track the origin of the entity'
    __slots__ = ()
    entity_origin = fields.Selection(
        [
            ('direct', 'Direct'),
            ('indirect', 'Indirect'),
        ], 'Entity Origin', states={'required': True}, sort=False,
        help='Defines, if an object was created as foreign object (indirect) '
             'or not.')
    entity_creator = fields.Many2One(
        'party.party', 'Entity Creator',
        states={'required': Eval('entity_origin') == 'indirect'},
        depends=['entity_origin'])

    @staticmethod
    def default_entity_origin():
        return "direct"


class MixinRight:
    'Mixin for the right a rightsholder claims on an rights object'
    __slots__ = ()
    type_of_right = fields.Selection(
        [
            ('copyright', 'Copyright'),
            ('ancillary', 'Ancillary Copyright'),
        ], 'Type of Right', required=True, help='Type of right')
    valid_from = fields.Date('Valid From Date')
    valid_to = fields.Date('Valid To Date')
    country = fields.Many2One(
        'country.country', 'Territory or Country', states={'required': True})
    collecting_society = fields.Many2One(
        'collecting_society', 'Collecting Society')

    @property
    def rightsholder(self):
        raise NotImplementedError("Subclasses should implement this")

    @property
    def rightsobject(self):
        raise NotImplementedError("Subclasses should implement this")

    @property
    def contribution(self):
        raise NotImplementedError("Subclasses should implement this")

    @property
    def predecessor(self):
        raise NotImplementedError("Subclasses should implement this")

    @property
    def successor(self):
        raise NotImplementedError("Subclasses should implement this")

    @staticmethod
    def default_country():
        Company = Pool().get('company.company')
        if Transaction().context.get('company'):
            company = Company(Transaction().context['company'])
            return company.party.address_get('country').country
        Country = Pool().get('country.country')
        country = Country.search(['code', '=', 'DE'])
        if country:
            return country[0]
        country = Country.search(['name', '=', 'None'])
        if country:
            return country[0]
        country = Country(name='None')
        country.save()
        return country


class MixinIdentifier:
    'Mixin for <Object>Identifier models'
    __slots__ = ()

    valid_from = fields.Date('Valid From Date')
    valid_to = fields.Date('Valid To Date')
    id_code = fields.Char('ID Code')


class MixinIdentifierHelper:
    'Mixin for Repertoire models that feature identifiers'
    __slots__ = ()

    # TODO: honor valid-from and -to dates

    def get_id_code(self, space):
        for identifier in self.cs_identifiers:
            if identifier.space.name == space:
                return identifier.id_code
        return None

    def set_id_code(self, space, id_code):
        replaced = False
        for identifier in self.cs_identifiers:
            if identifier.space.name == space:
                identifier.id_code = id_code
                identifier.save()
                replaced = True
        if not replaced:
            pool = Pool()
            Id = pool.get(self._fields['cs_identifiers'].model_name)
            Space = pool.get(Id._fields['space'].model_name)
            space = Space.search(['name', '=', space])
            if not space:
                return
            identifier = Id(space=space[0], id_code=id_code)
            self.cs_identifiers = [*self.cs_identifiers, identifier]


##############################################################################
# Collecting Society
##############################################################################

class CollectingSociety(PublicApi, ModelSQL, ModelView, CurrentState):
    'Collecting Society'
    __name__ = 'collecting_society'
    _history = True

    name = fields.Char(
        'Name', required=True, states=STATES, depends=DEPENDS)
    party = fields.Many2One(
        'party.party', 'Party', states=STATES, depends=DEPENDS,
        help='The legal person or organization acting the collecting society')
    represents_copyright = fields.Boolean(
        'Represents Copyright', help='The collecting society '
        'represents copyrights of authors')
    represents_ancillary_copyright = fields.Boolean(
        'Represents Ancillary Copyright', help='The collecting society '
        'represents ancillary copyights of performers')


# --- Tariffs -----------------------------------------------------------------

class TariffSystem(CodeSequence, ModelSQL, ModelView, CurrentState):
    'Tariff System'
    __name__ = 'tariff_system'
    _history = True
    _rec_name = 'version'
    _code_sequence = 'tariff_system_sequence'

    version = fields.Char(
        'Version', required=True, states=STATES, depends=DEPENDS)
    valid_from = fields.Date(
        'Valid from', help='Date from which the tariff is valid.')
    valid_through = fields.Date(
        'Valid through', help='Date thorugh which the tariff is valid.')
    transitional_through = fields.Date(
        'Transitional through',
        help='Date of the end of the transitinal phase, through which the '
        'tariff might still be used.')
    tariffs = fields.One2Many(
        'tariff_system.tariff', 'system', 'Tariffs',
        help='The tariffs of the tariff system.')
    # TODO: attachement

    @classmethod
    def __setup__(cls):
        super().__setup__()
        table = cls.__table__()
        cls._sql_constraints = [
            ('version_uniq', Unique(table, table.version),
             'The version of the tariff system must be unique.')
        ]

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            'OR',
            ('code',) + tuple(clause[1:]),
            ('version',) + tuple(clause[1:]),
        ]

    def get_rec_name(self, name):
        rec_name = f"v{self.version}"
        return rec_name


class TariffCategory(Code, PublicApi, ModelSQL, ModelView, CurrentState):
    'Tariff Category'
    __name__ = 'tariff_system.category'
    _history = True

    name = fields.Char(
        'Name', required=True, states=STATES, depends=DEPENDS)
    description = fields.Text(
        'Description', states=STATES, depends=DEPENDS,
        help='A description of the tariff category.')
    tariffs = fields.One2Many(
        'tariff_system.tariff', 'category', 'Tariffs',
        states=STATES, depends=DEPENDS,
        help='The tariffs in this tariff category.')

    adjustment_categories = fields.Many2Many(
        'tariff_category-tariff_adjustment_category',
        'tariff_category', 'tariff_adjustment_category',
        'Adjustment Categories',
        states=STATES, depends=DEPENDS,
        help='The adjustment categories applicable for the tariff category')
    relevance_categories = fields.Many2Many(
        'tariff_category-tariff_relevance_category',
        'tariff_category', 'tariff_relevance_category',
        'Relevance Categories',
        states=STATES, depends=DEPENDS,
        help='The relevance categories applicable for the tariff category')
    administration_product = fields.Many2One(
        'product.product', 'Administration Product', required=True,
        help="The product which represents the administration amount of the "
        "tariff.")
    distribution_product = fields.Many2One(
        'product.product', 'Distribution Product', required=True,
        help="The product which represents the distribution amount of the "
        "tariff.")

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            'OR',
            ('name',) + tuple(clause[1:]),
            ('code',) + tuple(clause[1:]),
        ]

    def get_rec_name(self, name):
        rec_name = f"{self.name}"
        return rec_name


class TariffAdjustmentCategory(Code, ModelSQL, ModelView, CurrentState):
    'Tariff Adjustment Category'
    __name__ = 'tariff_system.tariff.adjustment.category'
    _history = True

    name = fields.Char(
        'Name', states={'required': True}, depends=DEPENDS,
        help='The name of the category')
    value_min = fields.Numeric(
        'Minimum', digits=(3, 6), states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS, help='The minimum value')
    value_max = fields.Numeric(
        'Maximum', digits=(3, 6), states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS, help='The maximum value')
    value_default = fields.Numeric(
        'Default', digits=(3, 6), states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS, help='The default value')
    tariff_categories = fields.Many2Many(
        'tariff_category-tariff_adjustment_category',
        'tariff_adjustment_category', 'tariff_category', 'Tariff Categories',
        states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The tariff categories, for which the adjustment category can '
             'be applied')


class TariffCategoryTariffAdjustmentCategory(ModelSQL):
    'Tariff Category - Tariff Adjustment Category'
    __name__ = 'tariff_category-tariff_adjustment_category'
    _history = True
    tariff_category = fields.Many2One(
        'tariff_system.category', 'Tariff Category',
        required=True, ondelete='CASCADE')
    tariff_adjustment_category = fields.Many2One(
        'tariff_system.tariff.adjustment.category',
        'Tariff Adjustment Category',
        required=True, ondelete='CASCADE')


class TariffAdjustment(PublicApi, ModelSQL, ModelView):
    'Tariff Adjustment'
    __name__ = 'tariff_system.tariff.adjustment'
    _history = True

    category = fields.Many2One(
        'tariff_system.tariff.adjustment.category', 'Category',
        states={'required': True}, help='The category of the adjustment')
    status = fields.Selection(
        [
            ('on_approval', 'On Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ], 'Status', required=True, sort=False,
        help='The approval status of the adjustment')
    value = fields.Numeric(
        'Value', digits=(3, 6),
        required=True,
        # domain=[      using pre_validate() member instead
        #     ['OR',
        #         ('category', '=', None),
        #         ('category.value_min', '<=', Eval('value')),],
        #     ['OR',
        #         ('category', '=', None),
        #         ('category.value_max', '>=', Eval('value')),],
        #     ],
        help='The value of the adjustment')
    deviation = fields.Boolean(
        'Deviation', help='Does the value deviate from the category standard?')
    deviation_reason = fields.Text(
        'Deviation Reason', states={
            'required': Bool(Eval('deviation')),
            'invisible': Bool(~Eval('deviation')),
        }, depends=['deviation'],
        help='Reason for deviation')

    utilisation_indicators = fields.Many2One(
        'utilisation.indicators', 'Indicators Utilisation',
        help='The set of utilisation indicators of the tariff adjustment')

    @fields.depends('category')
    def on_change_category(self):
        if self.category:
            self.value = self.category.value_default

    @staticmethod
    def default_deviation():
        return False

    @staticmethod
    def default_status():
        return 'on_approval'

    def pre_validate(self):
        if (
            self.value < self.category.value_min
            or self.value > self.category.value_max
        ):
            raise UserError(
                f"The value '{self.value}' needs to be in the range "
                f"{self.category.value_min} to {self.category.value_max}."
            )
        super().pre_validate()


class TariffRelevanceCategory(PublicApi, ModelSQL, ModelView, CurrentState):
    'Tariff Relevance Category'
    __name__ = 'tariff_system.tariff.relevance.category'
    _history = True

    name = fields.Char(
        'Name', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The name of the category')
    value_min = fields.Numeric(
        'Minimum', digits=(3, 6), help='The minimum value', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS)
    value_max = fields.Numeric(
        'Maximum', digits=(3, 6), help='The maximum value', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS)
    value_default = fields.Numeric(
        'Default', digits=(3, 6), help='The default value', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS)
    tariff_categories = fields.Many2Many(
        'tariff_category-tariff_relevance_category',
        'tariff_relevance_category', 'tariff_category', 'Tariff Categories',
        states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The tariff categories, for which the relevance category can '
             'be applied')


class TariffCategoryTariffRelevanceCategory(ModelSQL):
    'Tariff Category - Tariff Relevance Category'
    __name__ = 'tariff_category-tariff_relevance_category'
    _history = True
    tariff_category = fields.Many2One(
        'tariff_system.category', 'Tariff Category',
        required=True, ondelete='CASCADE')
    tariff_relevance_category = fields.Many2One(
        'tariff_system.tariff.relevance.category', 'Tariff Relevance Category',
        required=True, ondelete='CASCADE')


class TariffRelevance(PublicApi, ModelSQL, ModelView):
    'Tariff Relevance'
    __name__ = 'tariff_system.tariff.relevance'
    _history = True

    category = fields.Many2One(
        'tariff_system.tariff.relevance.category', 'Category',
        states={'required': True},
        help='The category of the relevance')
    value = fields.Numeric(
        'Value', digits=(3, 6),
        required=True, help='The value of the relevance')
    deviation = fields.Boolean(
        'Deviation', help='Does the value deviate from the category standard?')
    deviation_reason = fields.Text(
        'Deviation Reason', states={
            'required': Bool(Eval('deviation')),
            'invisible': Bool(~Eval('deviation')),
        }, depends=['deviation'],
        help='Reason for deviation')

    # TODO: Many2One Interface
    utilisation_indicators = fields.One2Many(
        'utilisation.indicators', 'relevance', 'Indicators Utilisation',
        help='The set of utilisation indicators of the tariff relevance')

    @staticmethod
    def default_deviation():
        return False

    def get_rec_name(self, name):
        rec_name = f"{self.category.name}: {self.value:.2f}"
        if self.deviation:
            rec_name += " *"
        return rec_name

    @fields.depends('category')
    def on_change_category(self):
        if self.category:
            self.value = self.category.value_default

    def pre_validate(self):
        if (
            self.value < self.category.value_min
            or self.value > self.category.value_max
        ):
            raise UserError(
                f"The value '{self.value}' needs to be in the range "
                f"{self.category.value_min} to {self.category.value_max}."
            )
        super().pre_validate()


class Tariff(PublicApi, ModelSQL, ModelView, CurrentState):
    'Tariff'
    __name__ = 'tariff_system.tariff'
    _history = True

    name = fields.Function(
        fields.Char('Name'), 'get_name', searcher='search_name')
    code = fields.Function(
        fields.Char('Code'), 'get_code', searcher='search_code')
    system = fields.Many2One(
        'tariff_system', 'System', required=True)
    category = fields.Many2One(
        'tariff_system.category', 'Category', required=True)

    def get_name(self, name):
        return self.category.name

    def get_code(self, name):
        return self.category.code + self.system.version

    @classmethod
    def search_name(cls, name, clause):
        return [('tariff_system.tariff.' + clause[0],) + tuple(clause[1:])]

    @classmethod
    def search_code(cls, name, clause):
        return [('tariff_system.tariff.' + clause[0],) + tuple(clause[1:])]

    def get_base_formula(self):
        version = utils.convert_version(self.code)
        return getattr(collection, f"tariff_base__{version}")

    def get_relevance_formula(self):
        version = utils.convert_version(self.code)
        return getattr(collection, f"tariff_relevance__{version}")

    def get_share_formula(self):
        version = utils.convert_version(self.code)
        return getattr(collection, f"tariff_share__{version}")

    def get_adjustments_formula(self):
        version = utils.convert_version(self.code)
        return getattr(collection, f"tariff_adjustments__{version}")

    def get_total_formula(self):
        version = utils.convert_version(self.system.version)
        return getattr(collection, f"tariff_total__{version}")

    def get_fee_formula(self):
        version = utils.convert_version(self.system.version)
        return getattr(collection, f"tariff_fee__{version}")

    def get_rec_name(self, name):
        rec_name = self.category.code + self.system.version
        return rec_name


# --- Collection --------------------------------------------------------------

class Collection(CodeSequence, UUID, ModelSQL, ModelView, CurrencyDigits):
    """
    represents a number of allocations on an administrational level
    """
    __name__ = 'collection'
    _code_sequence = 'collection_sequence'

    start = fields.DateTime(
        'Start', states={'required': True},
        help='Start of the collection')
    end = fields.DateTime(
        'End', help='End of the collection')

    utilisations = fields.One2Many(
        'utilisation', 'collection', 'Utilisations',
        help='The collected utilisations')

    allocations = fields.One2Many(
        'allocation', 'collection', 'Total Allocations',
        help='The generated allocations')
    allocations_processing = fields.Function(
        fields.One2Many(
            'allocation', None, 'Processing Allocations',
            help="Allocations in state 'created' or 'calculated'"),
        'get_allocations_with_state')
    allocations_unposted = fields.Function(
        fields.One2Many(
            'allocation', None, 'Unposted Allocations',
            help="Allocations with drafted/validated invoices"),
        'get_allocations_with_state')
    allocations_posted = fields.Function(
        fields.One2Many(
            'allocation', None, 'Posted Allocations',
            help="Allocations with posted invoices"),
        'get_allocations_with_state')
    allocations_paid = fields.Function(
        fields.One2Many(
            'allocation', None, 'Paid Allocations',
            help="Allocations with paid invoices"),
        'get_allocations_with_state')
    allocations_distributed = fields.Function(
        fields.One2Many(
            'allocation', None, 'Distributed Allocations',
            help="Allocations in state 'distributed'"),
        'get_allocations_with_state')

    invoice_amount = fields.Function(
        fields.Numeric(
            'Invoice Amount', digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits'],
            help='The amount to collect'),
        'get_invoice_amount')

    entity_origin = fields.Selection(
        [
            ('automatic', 'Automatic'),
            ('manually', 'Manually'),
        ], 'Entity Origin', states={'required': True}, sort=False,
        help='Defines, if an object was created manually (e.g. staff) or '
             'automatic (e.g. cronjob).')
    entity_creator = fields.Many2One(
        'res.user', 'Entity Creator', states={'required': True})

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._order.insert(1, ('start', 'ASC'))
        # TODO:
        # - ensure allocations have the same origin (db level & tryton level)
        # - ensure allocations have the same licensee (db level & tryton level)

    def get_allocations_with_state(self, name):
        state = name.split("_")[-1]
        if state == 'processing':
            return [allocation
                    for allocation in self.allocations
                    if allocation.state in ['created', 'calculated']]
        elif state == 'unposted':
            return [allocation
                    for allocation in self.allocations
                    if allocation.invoice.state in ['draft', 'validated']]
        elif state == 'posted':
            return [allocation
                    for allocation in self.allocations
                    if allocation.invoice.state == 'posted']
        elif state == 'paid':
            return [allocation
                    for allocation in self.allocations
                    if allocation.state != 'distributed'
                    and allocation.invoice.state == 'paid']
        elif state == 'distributed':
            return [allocation
                    for allocation in self.allocations
                    if allocation.state == 'distributed']
        return []

    def get_invoice_amount(self, name):
        return sum([
            allocation.invoice_amount
            for allocation in self.allocations
        ])

    def create_allocations(self):
        # sanity checks
        if self.allocations:
            return

        # map utilisations to licensee
        licensee_utilisations = {}
        for utilisation in self.utilisations:
            licensee = utilisation.licensee.id
            if licensee not in licensee_utilisations:
                licensee_utilisations[licensee] = []
            licensee_utilisations[licensee].append(utilisation)

        # allocations
        pool = Pool()
        Allocation = pool.get('allocation')
        for licensee, utilisations in licensee_utilisations.items():
            allocation = Allocation(
                collection=self.id,
                state='created',
                licensee=licensee,
                utilisations=utilisations
            )
            allocation.save()
            for utilisation in utilisations:
                utilisation.state = 'allocated'
                utilisation.save()

    def calculate_allocations(self):
        for allocation in self.allocations:
            allocation.calculate_amounts()

    def create_invoices(self):
        for allocation in self.allocations:
            allocation.create_invoice()


class CollectStart(ModelView):
    """
    Defines the initial state of the Collect wizard, including a list of
    utilizarions to use in the allocation process.
    """

    __name__ = 'utilisation.allocation.collect.start'
    utilisations = fields.One2Many(
        'utilisation', None, 'Utilisations',
        states={'required': True}, help='The utilisations to allocate')
    entity_origin = fields.Selection(
        [
            ('automatic', 'Automatic'),
            ('manually', 'Manually'),
        ], 'Entity Origin', states={'required': True, 'invisible': True},
        help='Defines, if an object was created manually (e.g. staff) or '
             'automatic (e.g. cronjob).')

    @staticmethod
    def default_entity_origin():
        return 'manually'


class Collect(Wizard):
    """
    Defines states of the Collect wizard and holds the code for the
    allocation process.
    """
    __name__ = 'utilisation.allocation.collect'

    start = StateView(
        'utilisation.allocation.collect.start',
        'collecting_society.utilisation_allocation_collect_start_view_form',
        [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Collect', 'collect', 'tryton-ok', default=True),
        ])
    collect = StateTransition()

    def default_start(self, fields) -> dict[str, list['Utilisation']]:
        """
        triggered by the Collect button of the wizard

        Returns:
            List of Utilization that are preselected for collection in the
            wizard
        """
        utilisations = []
        if self.records:
            utilisations = [
                utilisation for utilisation in self.records
                if utilisation.state == 'finalized'
            ]
        else:
            pool = Pool()
            Utilisation = pool.get('utilisation')
            utilisations = Utilisation.search(['state', '=', 'finalized'])
        if not utilisations:
            if self.records:
                raise UserError('No Allocatable Utilisations',
                                'No finalized utilisations among %s'
                                % self.records)
            raise UserError('No Allocatable Utilisations',
                            'No finalized utilisations available')
        return {
            'utilisations': [utilisation.id for utilisation in utilisations]
        }

    def transition_collect(self):
        pool = Pool()
        Collection = pool.get('collection')
        collection = Collection(
            start=datetime.datetime.now(),
            entity_origin=self.start.entity_origin,
            entity_creator=Pool().get('res.user')(Transaction().user),
            utilisations=self.start.utilisations,
        )
        collection.save()
        collection.create_allocations()
        collection.calculate_allocations()
        collection.create_invoices()
        return 'end'


class Allocation(UUID, ModelSQL, ModelView, CurrencyDigits):
    'Allocation'
    __name__ = 'allocation'

    state = fields.Selection(
        [
            ('created', 'Created'),
            ('calculated', 'Calculated'),
            ('invoiced', 'Invoiced'),
            ('collected', 'Collected'),
            ('distributed', 'Distributed'),
        ], 'State', required=True, sort=False,
        help='The processing state of the allocation:\n\n'
        '*Created*: Default state for new allocations.\n'
        '*Calculated*: Amounts have been calculated '
        '(invoice amount, distribution amount, administration fee).\n'
        '*Invoiced*: An invoice for this allocation has been issued.\n'
        '*Collected*: The invoice has been payed and the allocation '
        'is ready to be distributed.\n'
        '*Distributed*: The distribution amount has been distributed.')

    licensee = fields.Many2One(
        'party.party', 'Licensee', states={'required': True},
        help="The licensee of the allocation")
    utilisations = fields.One2Many(
        'utilisation', 'allocation', 'Utilisations',
        help='The allocated utilisations')

    invoice_amount = fields.Numeric(
        'Invoice Amount', digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits'],
        help='The sum of invoice amounts over all utilisations')
    administration_fee = fields.Numeric(
        'Administration Fee', digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits'],
        help='The sum of adminstration fees over all utilisations')
    distribution_amount = fields.Function(
        fields.Numeric(
            'Distribution Amount', digits=(16, Eval('currency_digits', 2)),
            states={'readonly': True}, depends=['currency_digits'],
            help='The amount to distribute'),
        'on_change_with_distribution_amount')

    company = fields.Many2One(
        'company.company', 'Company', required=True)
    invoice = fields.One2One(
        'allocation-account.invoice', 'allocation', 'invoice',
        'Allocation Invoice',
        help='The invoice of the allocation')

    collection = fields.Many2One(
        'collection', 'Collection', required=True,
        help='The collection of the allocation')
    distribution = fields.Many2One(
        'distribution', 'Distribution',
        help='The distribution of the allocation')

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._order.insert(1, ('collection.start', 'ASC'))

    @staticmethod
    def default_company():
        return Transaction().context.get('company') or 1

    @fields.depends('invoice_amount', 'administration_fee')
    def on_change_with_distribution_amount(self, name=None):
        if not self.invoice_amount or not self.administration_fee:
            return None
        return self.invoice_amount - self.administration_fee

    def calculate_amounts(self):
        # sanity checks
        if self.state != 'created':
            return
        # amounts
        invoice_amount = Decimal('0')
        administration_fee = Decimal('0')
        for utilisation in self.utilisations:
            invoice_amount += utilisation.confirmed_invoice_amount
            administration_fee += utilisation.confirmed_administration_fee
        self.state = 'calculated'
        self.invoice_amount = invoice_amount
        self.administration_fee = administration_fee
        self.save()

    def _get_invoice(self):
        pool = Pool()
        Invoice = pool.get('account.invoice')
        Journal = pool.get('account.journal')

        journals = Journal.search([
            ('type', '=', 'revenue'),
        ], limit=1)
        if journals:
            journal, = journals
        else:
            journal = None

        data = {
            'allocation': self,
            'company': self.company,
            'type': 'out',
            'journal': journal,
            'party': self.licensee,
            'invoice_address': self.licensee.address_get('invoice'),
            'currency': self.company.currency,
            'account': self.licensee.account_receivable,
            'payment_term': self.licensee.customer_payment_term,
            'description': "Invoice Description",
            'invoice_date': datetime.date.today(),
        }
        return Invoice(**data)

    def create_invoice(self):
        '''
        Creates and returns an invoice
        '''
        pool = Pool()
        Invoice = pool.get('account.invoice')

        if not self.licensee.address_get('invoice'):
            raise UserError('Missing Invoice Address',
                            'The Licensee "%s" has no invoice address '
                            'assigned, so the allocation can\'t be invoiced.' %
                            self.licensee.rec_name,)
        if not self.licensee.account_receivable:
            raise UserError('Missing Account Receivable',
                            'The Licensee "%s" has no account receivable '
                            'assigned, so the allocation can\'t be invoiced.' %
                            self.licensee.rec_name,)

        invoice_lines = []
        for utilisation in self.utilisations:
            invoice_lines += utilisation._get_invoice_lines()
        if not invoice_lines:
            return
        invoice = self._get_invoice()
        invoice.lines = invoice_lines
        invoice.save()
        Invoice.update_taxes([invoice])
        if invoice.allocation:
            invoice.allocation.state = 'invoiced'
            invoice.allocation.save()
        return invoice


class AllocationAccountInvoice(ModelSQL):
    'Allocation - Invoice'
    __name__ = 'allocation-account.invoice'
    _history = True

    allocation = fields.Many2One(
        'allocation', 'Allocation', required=True, ondelete='CASCADE')
    invoice = fields.Many2One(
        'account.invoice', 'Invoice', required=True, ondelete='CASCADE')


class AllocationInvoice(Wizard):
    'Allocation Invoice'
    __name__ = 'allocation.invoice'
    start_state = 'invoice'
    invoice = StateAction('account_invoice.act_invoice_form')

    def do_invoice(self, action):
        pool = Pool()
        Allocation = pool.get('allocation')

        allocations = Allocation.browse(Transaction().context['active_ids'])
        invoices = []
        for allocation in allocations:
            invoice = Allocation.create_invoice(allocation)
            if invoice:
                invoices.append(invoice)

        data = {'res_id': [i.id for i in invoices]}
        if len(invoices) == 1:
            action['views'].reverse()
        return action, data


# --- Distribution ------------------------------------------------------------

class Distribution(CodeSequence, UUID, ModelSQL, ModelView, CurrencyDigits):
    'Distribution'
    __name__ = 'distribution'
    _code_sequence = 'distribution_sequence'

    start = fields.DateTime(
        'Start', states={'required': True},
        help='Start of the collection')
    end = fields.DateTime(
        'End', help='End of the collection')

    allocations = fields.One2Many(
        'allocation', 'distribution', 'Allocations',
        help='The distributed allocations')

    entity_origin = fields.Selection(
        [
            ('automatic', 'Automatic'),
            ('manually', 'Manually'),
        ], 'Entity Origin', states={'required': True}, sort=False,
        help='Defines, if an object was created manually (e.g. staff) or '
             'automatic (e.g. cronjob).')
    entity_creator = fields.Many2One(
        'res.user', 'Entity Creator', states={'required': True})

    invoice_amount = fields.Numeric(
        'Invoice Amount', digits=(16, Eval('currency_digits', 2)),
        states={'readonly': True}, depends=['currency_digits'],
        help='The invoice amount for the distribution')
    initial_general_amount = fields.Numeric(
        'Initial General Amount', digits=(16, Eval('currency_digits', 2)),
        states={'readonly': True}, depends=['currency_digits'],
        help='The initial general amount for the distribution')
    initial_distribution_amount = fields.Numeric(
        'Initial Distribution Amount', digits=(16, Eval('currency_digits', 2)),
        states={'readonly': True}, depends=['currency_digits'],
        help='The initial distribution amount for the distribution')
    adjusted_general_amount = fields.Numeric(
        'General Amount', digits=(16, Eval('currency_digits', 2)),
        states={'readonly': True}, depends=['currency_digits'],
        help='The adjusted general amount for the distribution')
    adjusted_distribution_amount = fields.Numeric(
        'Distribution Amount', digits=(16, Eval('currency_digits', 2)),
        states={'readonly': True}, depends=['currency_digits'],
        help='The adjusted distribution amount for the distribution')
    social_fund_amount = fields.Numeric(
        'Social Fund Amount', digits=(16, Eval('currency_digits', 2)),
        states={'readonly': True}, depends=['currency_digits'],
        help='The social fund amount')
    cultural_fund_amount = fields.Numeric(
        'Cultural Fund Amount', digits=(16, Eval('currency_digits', 2)),
        states={'readonly': True}, depends=['currency_digits'],
        help='The cultural fund amount')
    reserve_fund_amount = fields.Numeric(
        'Reserve Fund Amount', digits=(16, Eval('currency_digits', 2)),
        states={'readonly': True}, depends=['currency_digits'],
        help='The reserve fund amount')

    funds_account_move = fields.One2One(
        'distribution-account.move', 'distribution', 'move',
        'Funds Account Move',
        help='The account move for the funds')

    licenser_invoices = fields.One2Many(
        'account.invoice', 'distribution', 'Total Invoices',
        help='The invoices for the distribution')
    licenser_invoices_unposted = fields.Function(
        fields.One2Many(
            'account.invoice', None, 'Unposted Invoices',
            help="Drafted/Validated invoices"),
        'get_licenser_invoices_with_state')
    licenser_invoices_posted = fields.Function(
        fields.One2Many(
            'account.invoice', None, 'Posted Invoices',
            help="Posted invoices"),
        'get_licenser_invoices_with_state')
    licenser_invoices_paid = fields.Function(
        fields.One2Many(
            'account.invoice', None, 'Paid Invoices',
            help="Paid invoices"),
        'get_licenser_invoices_with_state')

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._order.insert(1, ('start', 'ASC'))

    @staticmethod
    def default_start():
        return datetime.datetime.now()

    def get_licenser_invoices_with_state(self, name):
        state = name.split("_")[-1]
        if state == 'unposted':
            return [invoice
                    for invoice in self.licenser_invoices
                    if invoice.state in ['draft', 'validated']]
        elif state == 'posted':
            return [invoice
                    for invoice in self.licenser_invoices
                    if invoice.state == 'posted']
        elif state == 'paid':
            return [invoice
                    for invoice in self.licenser_invoices
                    if invoice.state == 'paid']
        return []

    def distribute_allocations(self):
        # sanity checks
        assert all([
            allocation.state == 'collected'
            for allocation in self.allocations
        ]), f"not all allocations in {self} have the state 'collected'"

        # amounts
        invoice_amount = Decimal('0')
        general_amount = Decimal('0')
        distribution_amount = Decimal('0')
        for allocation in self.allocations:
            invoice_amount += allocation.invoice_amount
            for utilisation in allocation.utilisations:
                if utilisation.creation_list:
                    distribution_amount += utilisation.confirmed_invoice_amount
                else:
                    general_amount += utilisation.confirmed_invoice_amount

        assert invoice_amount == general_amount + distribution_amount, (
               f"invoice amount in distribution {self} is not the sum of "
               "general amount and distributed amount")

        self.invoice_amount = invoice_amount.quantize(
            Decimal(1) / 10 ** self.get_currency_digits(''))
        self.initial_general_amount = general_amount.quantize(
            Decimal(1) / 10 ** self.get_currency_digits(''))
        self.initial_distribution_amount = distribution_amount.quantize(
            Decimal(1) / 10 ** self.get_currency_digits(''))

        # distribution without shares
        if distribution_amount == 0:

            # caclulate corrected general/distribution amount
            self.adjusted_general_amount = self.initial_general_amount
            self.adjusted_distribution_amount = 0

            # caclulate fonds/reserve amounts
            social_fund_amount = general_amount / Decimal(3)
            cultural_fund_amount = general_amount / Decimal(3)
            reserve_fund_amount = general_amount / Decimal(3)

            assert math.isclose(general_amount,
                                sum([social_fund_amount,
                                     cultural_fund_amount,
                                     reserve_fund_amount])), (
                   "sum of funds is not close to general amount")

            self.social_fund_amount = social_fund_amount.quantize(
                Decimal(1) / 10 ** self.get_currency_digits(''))
            self.cultural_fund_amount = cultural_fund_amount.quantize(
                Decimal(1) / 10 ** self.get_currency_digits(''))
            self.reserve_fund_amount = reserve_fund_amount.quantize(
                Decimal(1) / 10 ** self.get_currency_digits(''))

        # distribute with shares
        else:

            # generate list of creation shares in invoice amount
            creation_shares = []
            for allocation in self.allocations:
                for utilisation in allocation.utilisations:
                    creation_list = utilisation.creation_list
                    if not creation_list:
                        continue
                    total_weight = sum(
                        [item.weight for item in creation_list.billable])
                    for item in creation_list.billable:
                        weight = (
                            utilisation.confirmed_invoice_amount
                            / distribution_amount
                            * Decimal(item.weight)
                            / Decimal(total_weight)
                        )
                        if not weight:
                            # exclude 0 amounts
                            continue
                        creation_shares.append({
                            'creation': item.creation,
                            'weight': weight,
                            'utilisation': utilisation,
                        })

            assert math.isclose(1, sum([share['weight']
                                        for share in creation_shares])), (
                   "sum of creation shares is not close to 1")

            # caclulate corrected general/distribution amount
            general_ratio = general_amount / invoice_amount
            if general_ratio < Decimal('0.1'):
                general_amount = invoice_amount * Decimal('0.1')
                distribution_amount = invoice_amount - general_amount
            elif general_ratio > Decimal('0.15'):
                general_amount = invoice_amount * Decimal('0.15')
                distribution_amount = invoice_amount - general_amount

            assert math.isclose(general_amount + distribution_amount,
                                invoice_amount), (
                   "sum of general and distribution amount differs from "
                   "invoice amount")

            self.adjusted_general_amount = general_amount.quantize(
                Decimal(1) / 10 ** self.get_currency_digits(''))
            self.adjusted_distribution_amount = distribution_amount.quantize(
                Decimal(1) / 10 ** self.get_currency_digits(''))

            # calcualte amounts for shares with adjusted distribution amount
            for creation_share in creation_shares:
                creation_share['amount'] = (
                    distribution_amount * creation_share['weight'])

            assert math.isclose(distribution_amount,
                                sum([share['amount']
                                     for share in creation_shares])), (
                   "sum of share amounts is not close to distribution amount")

            # caclulate fonds/reserve amounts
            social_fund_amount = general_amount / Decimal(3)
            cultural_fund_amount = general_amount / Decimal(3)
            reserve_fund_amount = general_amount / Decimal(3)

            assert math.isclose(general_amount,
                                sum([social_fund_amount,
                                     cultural_fund_amount,
                                     reserve_fund_amount])), (
                   "sum of funds is not close to general amount")

            self.social_fund_amount = social_fund_amount.quantize(
                Decimal(1) / 10 ** self.get_currency_digits(''))
            self.cultural_fund_amount = cultural_fund_amount.quantize(
                Decimal(1) / 10 ** self.get_currency_digits(''))
            self.reserve_fund_amount = reserve_fund_amount.quantize(
                Decimal(1) / 10 ** self.get_currency_digits(''))

            # generate list of licenser share amounts
            licenser_shares = []
            for share in creation_shares:
                version = utils.convert_version(
                    utilisation.distribution_plan.version)
                get_roles = getattr(distribution, f'roles__{version}')
                roles = get_roles(utilisation, share['creation'])
                split = distribution.Split(roles)
                if split.contains_rightsholders():
                    licenser_shares += split.distribute(share['amount'])
                    continue
                licenser_shares.append({
                    'licenser': None,
                    'amount': share['amount'],
                    'meta': {
                        'utilisation': utilisation.code,
                        'creation': share['creation'].code,
                        'undistributable': 'nolicenser'
                    },
                })

            assert math.isclose(distribution_amount,
                                sum([share['amount']
                                     for share in licenser_shares])), (
                   "sum of licenser shares not close to distribution amount")

            # group shares by licenser and tariff
            grouped_shares = {}
            for share in licenser_shares:
                licenser = share['licenser']
                tariff = share['utilisation'].tariff
                if licenser not in grouped_shares:
                    grouped_shares[licenser] = {}
                if tariff not in grouped_shares[licenser]:
                    grouped_shares[licenser][tariff] = {
                        'distribution': self,
                        'tariff': tariff,
                        'amount': Decimal(0),
                    }
                grouped_shares[licenser][tariff]['amount'] += share['amount']

            assert math.isclose(distribution_amount,
                                sum([share['amount']
                                     for tariffs in grouped_shares.values()
                                     for share in tariffs.values()])), (
                   "sum of grouped shares is not close to distribution amount")

        # post move for fonds
        pool = Pool()
        Move = pool.get('account.move')
        Journal = pool.get('account.journal')
        Company = pool.get('company.company')
        Period = pool.get('account.period')

        company = Company(Transaction().context['company'])
        period = Period.find(company.id, date=self.start.date())
        journal, = Journal.search([('code', '=', 'EXP')], limit=1)
        _move = {
            'journal': journal,
            'period': period,
            'date': self.start.date(),
            'origin': self,
            'company': company,
            'lines': self._get_funds_lines(),
        }
        move = Move(**_move)
        move.save()
        Move.post([move])
        self.funds_account_move = move

        # post invoices for licenser shares
        if distribution_amount > 0:
            Invoice = pool.get('account.invoice')
            invoices = []
            for licenser, tariffs in grouped_shares.items():
                _invoice = {
                    'distribution': self,
                    'company': company,
                    'type': 'in',
                    'journal': journal,
                    'party': licenser,
                    'invoice_address': licenser.address_get('invoice'),
                    'currency': company.currency,
                    'account': licenser.account_payable,
                    'description': "Invoice Description",
                    'invoice_date': datetime.date.today(),
                    'lines': self._get_share_invoice_lines(tariffs)
                }
                invoices.append(Invoice(**_invoice))
            Invoice.save(invoices)
            Invoice.update_taxes(invoices)
            Invoice.validate(invoices)
            Invoice.post(invoices)
            self.licenser_invoices = invoices

        # save
        self.save()
        for allocation in self.allocations:
            allocation.state = 'distributed'
            allocation.save()

    def _get_funds_lines(self):
        pool = Pool()
        Account = pool.get('account.account')
        account_debit, = Account.search([('code', '=', '8200')])
        account_social, = Account.search([('code', '=', '0950')])
        account_cultural, = Account.search([('code', '=', '0970')])
        account_reserve, = Account.search([('code', '=', '0974')])
        return [{
            # debit
            'account': account_debit,
            'debit': sum([
                self.social_fund_amount,
                self.cultural_fund_amount,
                self.reserve_fund_amount,
            ]),
            'credit': Decimal(0),
            'state': 'draft',
        }, {
            # credit: social fund
            'account': account_social,
            'debit': Decimal(0),
            'credit': self.social_fund_amount,
            'state': 'draft',
        }, {
            # credit: cultural fund
            'account': account_cultural,
            'debit': Decimal(0),
            'credit': self.cultural_fund_amount,
            'state': 'draft',
        }, {
            # credit: reserve fund
            'account': account_reserve,
            'debit': Decimal(0),
            'credit': self.reserve_fund_amount,
            'state': 'draft',
        }]

    def _get_share_invoice_lines(self, tariffs):
        pool = Pool()
        Account = pool.get('account.account')
        # Tax = pool.get('account.invoice.tax')

        account_royalties, = Account.search([('code', '=', '4126')])
        # tax7, = Tax.search(
        #     [('name', '=', "Umsatzsteuer – Ermäßigter Satz")], limit=1)

        lines = []
        total_amount = Decimal(0)
        for tariff, share in tariffs.items():
            amount = share['amount'].quantize(Decimal('0.00'))
            total_amount += amount
            # royalties
            lines.append({
                'account': account_royalties,
                'type': 'line',
                'description': f"Royalties {share['tariff'].code}",
                'origin': share['distribution'],
                'quantity': 1,
                'unit_price': amount,
                # 'taxes': [tax7],
                'invoice_type': 'in',
            })
        # administration fee
        lines.append({
            'account': account_royalties,
            'type': 'line',
            'description': "Administration Fee",
            'origin': share['distribution'],
            'quantity': 1,
            'unit_price': amount * Decimal('-0.1'),
            # 'taxes': None,
            'invoice_type': 'in',
        })
        # membership fee
        lines.append({
            'account': account_royalties,
            'type': 'line',
            'description': "Membership Fee",
            'origin': share['distribution'],
            'quantity': 1,
            'unit_price': Decimal('-123.45'),
            # 'taxes': None,
            'invoice_type': 'in',
        })
        # retirement provisions
        lines.append({
            'account': account_royalties,
            'type': 'line',
            'description': "Retirement Provisions",
            'origin': share['distribution'],
            'quantity': 1,
            'unit_price': Decimal('-12.34'),
            # 'taxes': None,
            'invoice_type': 'in',
        })
        return lines


class DistributionAccountMove(ModelSQL):
    'Distribution - AccountMove'
    __name__ = 'distribution-account.move'
    _history = True

    distribution = fields.Many2One(
        'distribution', 'Distribution', required=True, ondelete='CASCADE')
    move = fields.Many2One(
        'account.move', 'Move', required=True, ondelete='CASCADE')


class DistributionPlan(CodeSequence, ModelSQL, ModelView):
    'Distribution Plan'
    __name__ = 'distribution.plan'
    _history = True
    _code_sequence = 'distribution_plan_sequence'

    version = fields.Char(
        'Version', required=True)
    valid_from = fields.Date(
        'Valid from',
        help='Date from which the distribution plan is valid.')
    valid_through = fields.Date(
        'Valid through',
        help='Date thorugh which the distribution plan is valid.')
    transitional_through = fields.Date(
        'Transitional through',
        help='Date of the end of the transitinal phase, through which the '
        'tariff might still be used.')
    # TODO: attachement

    @classmethod
    def __setup__(cls):
        super().__setup__()
        table = cls.__table__()
        cls._sql_constraints = [
            ('version_uniq', Unique(table, table.version),
             'The version of the distribution plan must be unique.')
        ]

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            'OR',
            ('code',) + tuple(clause[1:]),
            ('version',) + tuple(clause[1:]),
        ]

    def get_rec_name(self, name):
        rec_name = f"v{self.version}"
        return rec_name


class DistributeStart(ModelView):
    'Distribute Start'
    __name__ = 'distribution.distribute.start'

    allocations = fields.One2Many(
        'allocation', None, 'Allocations',
        states={'required': True}, help='The Allocations to distribute')
    entity_origin = fields.Selection(
        [
            ('automatic', 'Automatic'),
            ('manually', 'Manually'),
        ], 'Entity Origin', states={'required': True, 'invisible': True},
        help='Defines, if an object was created manually (e.g. staff) or '
             'automatic (e.g. cronjob).')

    @staticmethod
    def default_entity_origin():
        return 'manually'


class Distribute(Wizard):
    "Distribute"
    __name__ = 'distribution.distribute'

    start = StateView(
        'distribution.distribute.start',
        'collecting_society.distribution_distribute_start_view_form',
        [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Start', 'distribute', 'tryton-ok', default=True),
        ])
    distribute = StateTransition()

    # @classmethod
    # def __setup__(cls):
    #     super().__setup__()
    #     cls.__rpc__['create'].fresh_session = True

    def default_start(self, fields):
        allocations = []
        if self.records:
            allocations = [
                allocation for allocation in self.records
                if allocation.state == 'collected'
            ]
        else:
            pool = Pool()
            Allocation = pool.get('allocation')
            allocations = Allocation.search(['state', '=', 'collected'])
        if not allocations:
            if self.records:
                raise UserError('No Distributable Allocations',
                                'No collected allocations among %s'
                                % self.records)
            raise UserError('No Distributable Allocations',
                            'No collected allocations available')
        return {
            'allocations': [allocation.id for allocation in allocations]
        }

    def transition_distribute(self):
        pool = Pool()
        Distribution = pool.get('distribution')
        distribution = Distribution(
            start=datetime.datetime.now(),
            entity_origin=self.start.entity_origin,
            entity_creator=Pool().get('res.user')(Transaction().user),
            allocations=self.start.allocations,
        )
        distribution.save()
        distribution.distribute_allocations()
        return 'end'


# --- Indicators --------------------------------------------------------------

class EventIndicators(ModelSQL, ModelView, CurrencyDigits):
    'Event Indicators'
    __name__ = 'event.indicators'
    _history = True

    start = fields.DateTime(
        'Start', help='Start of the event')
    end = fields.DateTime(
        'End', help='End of the event')
    attendants = fields.Integer(
        'Attendants', help='The number of attendants')
    max_attendants = fields.Integer(
        'Max Attendants', help='The maximum number of attendants')
    max_admission = fields.Numeric(
        'Max Admission', depends=['currency_digits'],
        digits=(16, Eval('currency_digits', 2)),
        help='The maxiumum entrance fee')
    turnover_tickets = fields.Numeric(
        'Turnover Tickets', depends=['currency_digits'],
        digits=(16, Eval('currency_digits', 2)),
        help='The ticket related turnover')
    turnover_benefit = fields.Numeric(
        'Turnover Benefit', depends=['currency_digits'],
        digits=(16, Eval('currency_digits', 2)),
        help='The benefit related turnover')
    expenses_musicians = fields.Numeric(
        'Expenses Musicians', depends=['currency_digits'],
        digits=(16, Eval('currency_digits', 2)),
        help='The expenses for the musicians')
    expenses_production = fields.Numeric(
        'Expenses Production', depends=['currency_digits'],
        digits=(16, Eval('currency_digits', 2)),
        help='The expenses for the production')

    @classmethod
    def write(cls, records, values, *args):
        super().write(records, values, *args)
        # recalculate estimated utilisations
        domain = [('context.estimated_indicators', 'in', records, 'event')]
        for utilisation in Utilisation.search(domain):
            if utilisation.state == 'estimated':
                utilisation.calculate_all('estimated', save=True)
        # recalculate confirmed utilisations
        domain = [('context.confirmed_indicators', 'in', records, 'event')]
        for utilisation in Utilisation.search(domain):
            if utilisation.state == 'confirmed':
                utilisation.calculate_all('confirmed', save=True)


class LocationIndicators(ModelSQL, ModelView, CurrencyDigits):
    'Location Indicators'
    __name__ = 'location.indicators'
    _history = True

    opening_hours = fields.One2Many(
        'location.indicators.period', 'location_indicators', 'Opening Hours',
        help='The opening hours of the location')
    opening_hours_duration = fields.Function(
        fields.Integer('Opening Hours Duration'), 'get_opening_hours_duration')
    turnover_gastronomy = fields.Numeric(
        'Turnover Gastronomy', depends=['currency_digits'],
        digits=(16, Eval('currency_digits', 2)),
        help='The gastronomy related turnover (e.g. food, drinks)')

    def get_opening_hours_duration(self, name):
        duration = 0
        for period in self.opening_hours:
            duration += period.duration
        return duration


class LocationIndicatorsPeriod(PublicApi, ModelSQL, ModelView):
    'Location Indicators Period'
    __name__ = 'location.indicators.period'
    _history = True

    weekdays = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    weekdays_mapping = {
        'monday': 1,
        'tuesday': 2,
        'wednesday': 3,
        'thursday': 4,
        'friday': 5,
        'saturday': 6,
        'sunday': 7,
    }

    location_indicators = fields.Many2One(
        'location.indicators', 'Location Indicators',
        states={'required': True}, help='The location indicators')

    start_weekday = fields.Selection(
        weekdays, 'Start Weekday', required=True, sort=False)
    start_time = fields.Time(
        'Start Time', format='%H:%M', required=True)

    end_weekday = fields.Selection(
        weekdays, 'End Weekday', required=True, sort=False)
    end_time = fields.Time(
        'End Time', format='%H:%M', required=True)

    duration = fields.Function(
        fields.Integer(
            'Duration', 'The duration of the period [h]'),
        'get_duration')

    def get_duration(self, name):
        start_day = self.weekdays_mapping[self.start_weekday]
        end_day = self.weekdays_mapping[self.end_weekday]
        # calculate hours within days
        duration_days = 1 + end_day - start_day
        if duration_days < 0:
            duration_days += 7
        duration_hours = duration_days * 24
        # substract hours of first day
        start_hour = self.start_time.hour
        start_minute = self.start_time.minute
        if start_minute >= 30:
            start_hour += 1
        duration_hours -= start_hour
        # substract hours of last day
        end_hour = self.end_time.hour
        end_minute = self.end_time.minute
        if end_minute >= 30:
            end_hour += 1
        duration_hours -= 24 - end_hour
        return duration_hours


class LocationSpaceIndicators(ModelSQL, ModelView):
    'Location Space Indicators'
    __name__ = 'location.space.indicators'
    _history = True

    size = fields.Float(
        'Size', digits=(10, 14),
        help='The size of the location space [squaremeter]')


class WebsiteResourceIndicators(ModelSQL, ModelView, CurrencyDigits):
    'Website Resource Indicators'
    __name__ = 'website.resource.indicators'
    _history = True

    streams = fields.Integer(
        'Streams', help='The number of streams')
    downloads = fields.Integer(
        'Downloads', help='The number of downloads')
    turnover_ads = fields.Numeric(
        'Turnover Ads', depends=['currency_digits'],
        digits=(16, Eval('currency_digits', 2)),
        help='The ads related turnover')
    turnover_sale = fields.Numeric(
        'Turnover Sale', depends=['currency_digits'],
        digits=(16, Eval('currency_digits', 2)),
        help='The sale related turnover')


class ReleaseIndicators(ModelSQL, ModelView):
    'Release Indicators'
    __name__ = 'release.indicators'
    _history = True

    copies = fields.Integer(
        'Copies', help='The number of copies')


class UtilisationIndicators(ModelSQL, ModelView, CurrencyDigits):
    'Utilisation Indicators'
    __name__ = 'utilisation.indicators'
    _history = True

    base = fields.Numeric(
        'Base', digits=(16, Eval('currency_digits', 2)),
        states={'readonly': True}, depends=['currency_digits'],
        help='The base value')
    relevance = fields.Many2One(
        'tariff_system.tariff.relevance', 'Relevance',
        help='The relevance')
    adjustments = fields.One2Many(
        'tariff_system.tariff.adjustment', 'utilisation_indicators',
        'Adjustments',
        help='The adjustments')

    invoice_amount = fields.Numeric(
        'Invoice Amount', digits=(16, Eval('currency_digits', 2)),
        states={'readonly': True}, depends=['currency_digits'],
        help='The amount to invoice')
    administration_fee = fields.Numeric(
        'Administration Amount', digits=(16, Eval('currency_digits', 2)),
        states={'readonly': True}, depends=['currency_digits'],
        help='The fee for administration')
    distribution_amount = fields.Function(
        fields.Numeric(
            'Distribution Amount', digits=(16, Eval('currency_digits', 2)),
            states={'readonly': True}, depends=['currency_digits'],
            help='The amount to distribute'),
        'on_change_with_distribution_amount')

    @fields.depends('invoice_amount', 'administration_fee')
    def on_change_with_distribution_amount(self, name=None):
        if not self.invoice_amount or not self.administration_fee:
            return None
        return self.invoice_amount - self.administration_fee

    def get_rec_name(self, name):
        sample = None
        utilisation = None
        if self.confirmed_utilisations:
            utilisation = self.confirmed_utilisations[0]
            sample = "Confirmed"
        elif self.estimated_utilisations:
            utilisation = self.estimated_utilisations[0]
            sample = "Estimated"
        if not utilisation:
            return None
        declaration = utilisation.declaration
        rec_name = (f"{sample} Indicators of Declaration "
                    f"{declaration.get_rec_name('')}")
        return rec_name

    # @fields.depends('adjustments', 'invoice_amount', 'administration_fee')
    # def on_change_adjustments(self):
    #     samples = ['estimated', 'confirmed']
    #     for sample in samples:
    #         for utilisation in getattr(self, f'{sample}_utilisations', []):
    #             setattr(utilisation, f'{sample}_indicators', self)
    #             self.invoice_amount = \
    #                 utilisation.calculate_invoice_amount(sample)
    #             self.administration_fee = \
    #                 utilisation.calculate_administration_fee(sample)
    #
    # @fields.depends('adjustments', 'invoice_amount', 'administration_fee')
    # def on_change_relevance(self):
    #     samples = ['estimated', 'confirmed']
    #     for sample in samples:
    #         for utilisation in getattr(self, f'{sample}_utilisations', []):
    #             setattr(utilisation, f'{sample}_indicators', self)
    #             self.invoice_amount = \
    #                 utilisation.calculate_invoice_amount(sample)
    #             self.administration_fee = \
    #                 utilisation.calculate_administration_fee(sample)


class IndicatorsMeta(ModelMeta):
    """
    Metaclass for models to be measured by indicators.

    Measured models are models of real world objects to be measured by a set of
    attributes. Indicators are models containing the set of attributes. Each
    measured model is expected to have exactly one corresponding indicator
    model and may refer to several samples of this indicator model.

    This metaclass prepares measured models to be used with indicators by:

    - adding Many2One fields to the measured model for each sample
    - adding One2Many fields to the indicators model for each sample
    - adding getter/setter for all indicator attributes in the measured model
    - autocreating the relations to the indicators in the measured model

    To add this metaclass to a measured model, it needs to have set:

        class ModelName(metaclass=IndicatorsMeta)
        __indicators__ = <INDICATORS_MODEL_NAME>
        __samples__ = [<SAMPLE_NAME_1>, <SAMPLE_NAME_2>]

    Example:

        Events(metaclass=IndicatorsMeta)
        __indicators__ = 'events.indicators'
        __samples__ = ['estimated', 'confirmed']

    If the indicator model would include one field 'size' and the samples would
    be 'estimated' and 'confirmed', the attributes would be accesible via
    `estimated_size` and `confirmed_size` in the measured model. The indicators
    are accessible via `estimated_indicators` and `confirmed_indicators`.

    Changes to the measured model:

    - Adds fields for the indicators for each sample
        - [fields.Many2One] <SAMPLE_NAME>_indicators
    - Adds create classmethod to autocreate the indicators objects
        - [classmethod] create
    - Adds copy classmethod to prevent copy of One2Many indicator fields
        - [classmethod] copy
    - Adds shortcut function fields with setter/getter for indicator attributes
        - [fields.Function] <SAMPLE_NAME>_<ATTRIBUTE_NAME>
        - [method] get_<SAMPLE_NAME>_<ATTRIBUTE_NAME>
        - [method] set_<SAMPLE_NAME>_<ATTRIBUTE_NAME>
    - Adds original field name in shortcut fields to ease later access:
        - [string] estimated_<ATTRIBUTE_NAME>._attribute_name
        - [string] confirmed_<ATTRIBUTE_NAME>._attribute_name

    Changes to the indicators model:
    - Adds back reference field to the measured for each sample
        - [fields.One2Many] <SAMPLE_NAME>_<MEASURED_MODEL_NAME>
    - Add set of measured field names to the indicator model
        - [set] _measured_field_names
    - Adds copy classmethod to prevent copy of One2Many indicator fields
        - [classmethod] copy

    Note: The class name of the indicator model is expected to be the
    capitalized model name without dots.
    """

    @staticmethod
    def dummy_create():
        """Dummy create method added, if none is present"""
        def create(cls, vlist):
            return super().create(vlist)
        return classmethod(create)

    @staticmethod
    def dummy_copy():
        """Dummy copy method added, if none is present"""
        def copy(cls, instances, default=None):
            super().copy(instances, default=default)
        return classmethod(copy)

    @staticmethod
    def indicator__copy():
        """This create method wraps the copy method of the indicator class"""
        def copy(cls, indicator_instances, default=None):
            if default is None:
                default = {}
            default = default.copy()
            # prevent copy of One2Many indicator fields
            for field_name in cls._measured_field_names:
                default[field_name] = None
            return cls._copy(indicator_instances, default=default)
        return classmethod(copy)

    @staticmethod
    def measured__create(indicators_model_name, samples):
        """This copy method wraps the create method of the measured class"""
        def create(cls, vlist):
            for entry in vlist:
                # autocreate indicator model
                for sample_name in samples:
                    if sample_name == 'confirmed':
                        continue
                    IndicatorsModel = Pool().get(indicators_model_name)
                    indicators, = IndicatorsModel.create([{}])
                    indicators.save()
                    entry[f'{sample_name}_indicators'] = indicators.id
            return cls._create(vlist)
        return classmethod(create)

    @staticmethod
    def measured__copy(samples):
        """This create method wraps the copy method of the measured class"""
        def copy(cls, measured_instances, default=None):
            if default is None:
                default = {}
            default = default.copy()
            # prevent copy of One2Many indicator fields
            for sample_name in samples:
                field_name = f'{sample_name}_indicators'
                if field_name in default:
                    default[field_name] = None
            return cls._copy(measured_instances, default=default)
        return classmethod(copy)

    @staticmethod
    def measured__get_attribute(sample_name):
        def get_value(self, name):
            indicators = getattr(self, f'{sample_name}_indicators')
            if indicators:
                attribute_name = getattr(self.__class__, name)._attribute_name
                value = getattr(indicators, attribute_name)
                if isinstance(value, tuple):
                    return [entry.id for entry in value]
                if isinstance(value, ModelSQL):
                    return value.id
                return value
        return get_value

    @staticmethod
    def measured__set_attribute(sample_name):
        def set_value(cls, measured_instances, name, value):
            for instance in measured_instances:
                attribute_name = getattr(cls, name)._attribute_name
                indicators = getattr(instance, f'{sample_name}_indicators')
                if indicators:
                    indicators.write([indicators], {attribute_name: value})
        return classmethod(set_value)

    @staticmethod
    def measured__search_attribute(sample_name):
        def search(cls, name, clause):
            attribute_name = getattr(cls, name)._attribute_name
            key = f'{sample_name}_indicators.{attribute_name}'
            return [
                (key,) + tuple(clause[1:]),
            ]
        return classmethod(search)

    def __new__(cls, measured_class_name, bases, dct):
        # execute PoolMeta.__new__()
        new = super().__new__(cls, measured_class_name, bases, dct)

        # sanity checks
        assert dct['__indicators__']
        assert dct['__samples__']

        # get model/class name and class of the indicators object
        samples = dct['__samples__']
        measured_model_name = dct['__name__']
        indicators_model_name = dct['__indicators__']
        indicators_class_name = "".join([
            part.capitalize() for part in indicators_model_name.split('.')])
        IndicatorsClass = getattr(sys.modules[__name__], indicators_class_name)

        # add copy classmethod to indicator class to prevent copy of backlinks
        if not hasattr(IndicatorsClass, '_copy'):
            if hasattr(IndicatorsClass, 'copy'):
                IndicatorsClass._copy = IndicatorsClass.copy
            else:
                setattr(IndicatorsClass, '_copy', cls.dummy_copy())
            setattr(IndicatorsClass, 'copy', cls.indicator__copy())

        # add create classmethod to autocreate the indicators objects
        if hasattr(new, 'create'):
            new._create = new.create
        else:
            setattr(new, '_create', cls.dummy_create())
        setattr(new, 'create', cls.measured__create(
                indicators_model_name, samples))
        # add copy classmethod to prevent copy of One2Many indicator fields
        if hasattr(new, 'copy'):
            new._copy = new.copy
        else:
            setattr(new, '_copy', cls.dummy_copy())
        setattr(new, 'copy', cls.measured__copy(samples))

        # for each sample
        for sample_name in samples:

            # add indicators field to the measured model
            indicators_field_name = f'{sample_name}_indicators'
            indicators_field_description = (
                f'{sample_name.capitalize()} Indicators'
            )
            setattr(new, indicators_field_name,
                    fields.Many2One(
                        indicators_model_name, indicators_field_description))

            # add getter/setter for all attributes in the indicators model
            for attribute_name, field in IndicatorsClass.__dict__.items():
                if isinstance(field, Field):
                    # ignore back references
                    if getattr(field, '_backreference', False):
                        continue
                    # function field name (e.g. estimated_turnover)
                    field_name = f'{sample_name}_{attribute_name}'
                    # add function field
                    function_field = copy.deepcopy(field)
                    if 'readonly' not in function_field.states:
                        function_field.states['readonly'] = ~Bool(
                            Eval(indicators_field_name))
                    getter_name = f'get_{field_name}'
                    setter_name = f'set_{field_name}'
                    searcher_name = f'search_{field_name}'
                    setattr(new, field_name,
                            fields.Function(function_field,
                                            getter_name,
                                            setter=setter_name,
                                            searcher=searcher_name))
                    # save original field name in field to ease later access
                    getattr(new, field_name)._attribute_name = attribute_name
                    # getter
                    if not getattr(new, getter_name, False):
                        setattr(new, getter_name,
                                cls.measured__get_attribute(sample_name))
                    # setter
                    if not getattr(new, setter_name, False):
                        setattr(new, setter_name,
                                cls.measured__set_attribute(sample_name))
                    # searcher
                    if not getattr(new, searcher_name, False):
                        setattr(new, searcher_name,
                                cls.measured__search_attribute(sample_name))

            # add back reference to the indicator model
            measured_field_name = '%s_%ss' % (
                sample_name, measured_model_name.replace('.', '_'))
            measured_field_description = '%s %ss' % (
                sample_name.capitalize(), measured_class_name)
            field = fields.One2Many(
                measured_model_name, indicators_field_name,
                measured_field_description, states={
                    'readonly': True,
                    'invisible': ~Bool(Eval(measured_field_name))
                }, depends=[measured_field_name])
            field._backreference = True
            setattr(IndicatorsClass, measured_field_name, field)

            # add set of measured field names to the indicator model
            if not getattr(IndicatorsClass, '_measured_field_names', False):
                setattr(IndicatorsClass, '_measured_field_names', set())
            IndicatorsClass._measured_field_names.add(measured_field_name)

        return new


##############################################################################
# Licenser
##############################################################################

class License(Code, PublicApi, ModelSQL, ModelView, CurrentState):
    'License'
    __name__ = 'license'
    _history = True

    name = fields.Char('Name', required=True)
    billable = fields.Boolean('Billable')
    freedom_rank = fields.Integer('Freedom Rank')
    version = fields.Char('Version', required=True)
    country = fields.Char('Country', required=True)
    link = fields.Char('Link', required=True)

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._order.insert(1, ('freedom_rank', 'ASC'))

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            'OR',
            ('code',) + tuple(clause[1:]),
            ('name',) + tuple(clause[1:]),
        ]


class Artist(CodeSequence, PublicApi, ModelSQL, ModelView, EntityOrigin,
             AccessControlList, CurrentState, MixinIdentifierHelper,
             ClaimState, CommitState):
    'Artist'
    __name__ = 'artist'
    _history = True
    _code_sequence = 'artist_sequence'

    name = fields.Char(
        'Name', required=True, states=STATES, depends=DEPENDS)
    party = fields.Many2One(
        'party.party', 'Party', states=STATES, depends=DEPENDS,
        help='The legal person or organization acting the artist')
    group = fields.Boolean(
        'Group', states={
            'readonly': Or(
                ~Eval('active'),
                Bool(Eval('group_artists')),
                Bool(Eval('solo_artists')),
            ),
        }, depends=DEPENDS + ['group_artists', 'solo_artists'],
        help='Check, if artist is a group of other artists, '
        'otherwise the artist is a solo artist')
    solo_artists = fields.Many2Many(
        'artist-artist', 'group_artist', 'solo_artist',
        'Solo Artists', domain=[
            ('group', '=', False),
        ], states={
            'readonly': ~Eval('active'),
            'invisible': ~Eval('group'),
        }, depends=['active', 'group'],
        help='The membering solo artists of this group')
    group_artists = fields.Many2Many(
        'artist-artist', 'solo_artist', 'group_artist',
        'Group Artists', domain=[
            ('group', '=', True),
        ], states={
            'readonly': ~Eval('active'),
            'invisible': Bool(Eval('group')),
        }, depends=['active', 'group'],
        help='The groups this solo artist is member of')
    releases = fields.Many2Many(
        'artist-release', 'artist', 'release', 'Releases',
        help='The releases, which belongs to the artist')
    creations = fields.One2Many(
        'creation', 'artist', 'Creations', states=STATES,
        depends=DEPENDS, help='The creations, which belong to the artist.')
    # TODO: remove access_parties, change payee workflow to acl
    access_parties = fields.Function(
        fields.Many2Many(
            'party.party', None, None, 'Access Parties',
            help='Shows the collection of all parties with access '
            'permissions to this artist'),
        'get_access_parties')
    invitation_token = fields.Char(
        'Invitation Token', help='The invitation token of a web user '
        'to claim this artist')
    description = fields.Text(
        'Description', states=STATES, depends=DEPENDS,
        help='A description of the artist')
    picture_data = fields.Binary(
        'Picture Data', states=STATES, depends=DEPENDS,
        help='Picture data of a photograph or logo')
    picture_data_md5 = fields.Char(
        'Picture Data Hash', states=STATES, depends=DEPENDS,
        help='The md5 hash of the picture data, also acting as ressouce name.')
    picture_thumbnail_data = fields.Binary(
        'Thumbnail Data', states=STATES, depends=DEPENDS,
        help='Thumbnail data of the picture')
    picture_data_mime_type = fields.Char(
        'Picture Data Mime Type', states=STATES, depends=DEPENDS,
        help='The mime type of picture data.')
    payee = fields.Many2One(
        'party.party', 'Payee',
        domain=[('id', 'in', Eval('access_parties', []))],
        states={
            'readonly': Or(
                ~Eval('active'),
                Bool(Eval('valid_payee')),
            ),
        },
        depends=DEPENDS + ['access_parties', 'group_artists', 'solo_artists'],
        help='The actual payee party of this artist which is '
        'responsible for earnings of this artist')
    payee_proposal = fields.Many2One(
        'party.party', 'Payee Proposal',
        domain=[('id', 'in', Eval('access_parties', []))],
        states=STATES, depends=DEPENDS + ['access_parties'],
        help='The proposed payee party of this artist')
    payee_acceptances = fields.Many2Many(
        'artist.payee.acceptance', 'artist', 'party', 'Payee Acceptances',
        domain=[('id', 'in', Eval('access_parties', []))],
        states=STATES, depends=DEPENDS + ['access_parties'],
        help='The parties which accepts the payee proposal')
    valid_payee = fields.Boolean(
        'Valid Payee', states={
            'readonly': Or(
                ~Eval('active'),
                ~Bool(Eval('payee')),
            ),
        }, depends=DEPENDS + ['payee'],
        help='Check, if the payee is manually validated by '
        'administration.')
    bank_account_number = fields.Many2One(
        'bank.account.number', 'Bank Account Number', states={
            'readonly': ~Bool(Eval('payee'))},
        domain=[('id', 'in', Eval('bank_account_numbers'))],
        depends=['payee', 'bank_account_numbers'],
        help='The bank account number for this artist')
    bank_account_numbers = fields.Function(
        fields.Many2Many(
            'bank.account.number', None, None, 'Bank Account Numbers',
            help='Shows the collection of all available bank account '
            'numbers of this artist'),
        'on_change_with_bank_account_numbers')
    bank_account_owner = fields.Function(
        fields.Many2One(
            'party.party', 'Bank Account Owner', states={
                'readonly': (
                    Or(
                        ~Bool(Eval('payee')),
                        ~Bool(Eval('bank_account_number'))))},
            help='Shows the bank account owner for this artist',
            depends=['payee', 'bank_account_number']),
        'on_change_with_bank_account_owner')
    cs_identifiers = fields.One2Many(
        'artist.cs_identifier', 'artist', '3rd-Party Identifier',)

    @classmethod
    def __setup__(cls):
        super().__setup__()
        table = cls.__table__()
        cls._sql_constraints = [
            ('invitation_token_uniq', Unique(table, table.invitation_token),
             'The invitation token of the artist must be unique.'),
        ]
        cls._order.insert(1, ('name', 'ASC'))

    @staticmethod
    def default_invitation_token():
        return str(uuid.uuid4())

    @classmethod
    def validate(cls, artists):
        super().validate(artists)
        for artist in artists:
            artist.check_name()

    def check_name(self):
        if SEPARATOR in self.name:
            self.raise_user_error('wrong_name', (self.name,))

    @classmethod
    def get_access_parties(cls, artists, name):
        parties = {}
        for artist in artists:
            parties[artist.id] = []
            if artist.party:
                parties[artist.id] += [artist.party.id]
            if artist.solo_artists:
                for solo_artist in artist.solo_artists:
                    if solo_artist.party:
                        parties[artist.id] += [solo_artist.party.id]
        return parties

    @fields.depends('party', '_parent_party.id', 'access_parties')
    def on_change_with_bank_account_numbers(self, name=None):
        BankAccountNumber = Pool().get('bank.account.number')

        bank_account_numbers = BankAccountNumber.search(
            [
                'OR', [
                    (
                        'account.owner.id', 'in', [
                            p.id for p in self.access_parties])
                ], [
                    ('account.owner.id', '=', self.party.id
                        if self.party else None),
                ]
            ])
        return bank_account_numbers or None

    @fields.depends('bank_account_number')
    def on_change_with_bank_account_owner(self, name=None):
        if self.bank_account_number:
            bank_account_owner = (
                self.bank_account_number.account.owner)
        else:
            bank_account_owner = None
        return bank_account_owner

    @fields.depends('payee')
    def on_change_payee(self):
        if self.payee:
            self.payee_acceptances = ()
            self.valid_payee = False
            self.payee_proposal = None

    @fields.depends('payee_proposal')
    def on_change_payee_proposal(self):
        if self.payee_proposal:
            self.payee_acceptances = ()
            self.valid_payee = False

    @classmethod
    def create(cls, vlist):
        default_roles = [('add', [
            r.id for r in
            AccessRole.search([('name', 'in', DEFAULT_ACCESS_ROLES)])])]

        acls = {}
        elist = super().create(vlist)
        for entry in elist:
            if entry.acl:
                continue
            # only normally created artists
            if entry.entity_origin != 'direct':
                continue
            # solo
            if entry.party and entry.party.web_user:
                acls[entry.party.web_user.id] = {
                    'entity': str(entry),
                    'web_user': entry.party.web_user.id,
                    'roles': default_roles
                }
            # group
            for member in entry.solo_artists:
                if not member.party or not member.party.web_user:
                    continue
                acls[member.party.web_user.id] = {
                    'entity': str(entry),
                    'web_user': member.party.web_user.id,
                    'roles': default_roles
                }
            # always autocreate creator acl
            if entry.entity_creator and entry.entity_creator.web_user:
                acls[entry.entity_creator.web_user.id] = {
                    'entity': str(entry),
                    'web_user': entry.entity_creator.web_user.id,
                    'roles': default_roles
                }
        AccessControlEntry.create(list(acls.values()))

        return elist

    @classmethod
    def write(cls, *args):
        default_roles = [('add', [
            r.id for r in
            AccessRole.search([('name', 'in', DEFAULT_ACCESS_ROLES)])])]
        actions = iter(args)
        args = []
        for artists, values in zip(actions, actions):
            for artist in artists:
                remaining = []
                for action, member_ids in values.get('solo_artists', []):
                    # add aces if not present
                    if action == 'add':
                        for member_id in member_ids:
                            member = cls.search([('id', '=', member_id)])
                            if not member:
                                continue
                            member = member[0]
                            if not member.party or not member.party.web_user:
                                continue
                            remaining.append(member.party.web_user.id)
                            ace = AccessControlEntry.search([
                                ('entity', '=', str(artist)),
                                ('web_user', '=', member.party.web_user)])
                            if ace:  # keep existing ace
                                continue
                            AccessControlEntry.create([{
                                'entity': str(artist),
                                'web_user': member.party.web_user.id,
                                'roles': default_roles}])
                    # remove existing aces
                    if action == 'remove':
                        for member_id in member_ids:
                            member = cls.search([('id', '=', member_id)])
                            if not member:
                                continue
                            member = member[0]
                            if not member.party or not member.party.web_user:
                                continue
                            # prevent deletion for members with same web_user
                            if member.party.web_user.id in remaining:
                                continue
                            ace = AccessControlEntry.search([
                                ('entity', '=', str(artist)),
                                ('web_user', '=', member.party.web_user)])
                            if not ace:
                                continue
                            AccessControlEntry.delete(ace)
            args.extend((artists, values))
        super().write(*args)

    @classmethod
    def delete(cls, records):
        for record in records:
            if record.group or record.solo_artists:
                record.solo_artists = []
                record.save()
        return super().delete(records)

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            'OR',
            ('code',) + tuple(clause[1:]),
            ('name',) + tuple(clause[1:]),
        ]


class ArtistArtist(ModelSQL):
    'Artist - Artist'
    __name__ = 'artist-artist'
    _history = True
    group_artist = fields.Many2One(
        'artist', 'Group Artist', required=True,
        ondelete='CASCADE')
    solo_artist = fields.Many2One(
        'artist', 'Solo Artist', required=True,
        ondelete='CASCADE')


class ArtistRelease(ModelSQL):
    'ArtistRelease'
    __name__ = 'artist-release'
    _history = True
    artist = fields.Many2One(
        'artist', 'Artist', required=True, ondelete='CASCADE')
    release = fields.Many2One(
        'release', 'Release', required=True, ondelete='CASCADE')


class ArtistPayeeAcceptance(ModelSQL):
    'Artist Payee Acceptance'
    __name__ = 'artist.payee.acceptance'
    _history = True
    artist = fields.Many2One(
        'artist', 'Artist', required=True, ondelete='CASCADE')
    party = fields.Many2One(
        'party.party', 'Party', required=True, ondelete='CASCADE')


class ArtistIdentifier(ModelSQL, ModelView, MixinIdentifier):
    'Artist Identifier'
    __name__ = 'artist.cs_identifier'
    _history = True
    space = fields.Many2One(
        'artist.cs_identifier.space', 'Artist Identifier Space',
        required=True, ondelete='CASCADE')
    artist = fields.Many2One(
        'artist', 'Artist',
        required=True, ondelete='CASCADE')


class ArtistIdentifierSpace(ModelSQL, ModelView):
    'Artist Identifier Space'
    __name__ = 'artist.cs_identifier.space'
    _history = True
    name = fields.Char('Name of the ID space')
    version = fields.Char('Version')


class ArtistPlaylist(PublicApi, ModelSQL, ModelView, EntityOrigin):
    'Artist Playlist'
    __name__ = 'artist.playlist'
    artist = fields.Many2One(
        'artist', 'Artist', states={'required': True},
        help='The artist of the playlist')
    public = fields.Boolean(
        'Public', help='Is the playlist accessible to other web users?')
    template = fields.Boolean(
        'Template', help='Is the playlist a template?')
    performance = fields.One2Many(
        'event.performance', 'playlist', 'Performance',
        help='The performance, where the playlist was used')
    items = fields.One2Many(
        'artist.playlist.item', 'playlist', 'Items',
        order=[('position', 'ASC')], help='The items in the playlist')


class ArtistPlaylistItem(PublicApi, ModelSQL, ModelView, EntityOrigin):
    'Artist Playlist Item'
    __name__ = 'artist.playlist.item'
    playlist = fields.Many2One(
        'artist.playlist', 'Playlist', required=True,
        help='The playlist of the item')
    creation = fields.Many2One(
        'creation', 'Creation', required=True,
        help='The creation of the item')
    position = fields.Integer(
        'Position', required=True,
        help='The sequence number of the item')


class Creation(CodeSequence, PublicApi, ModelSQL, ModelView, EntityOrigin,
               AccessControlList, CurrentState,
               ClaimState, CommitState):
    'Creation'
    __name__ = 'creation'
    _history = True
    _code_sequence = 'creation_sequence'
    distribution_type_selection = [
        ('original', 'Original'),
        ('cover', 'Cover'),
        ('adaption', 'Adaption'),
        ('remix', 'Remix'),
    ]

    title = fields.Char(
        'Title', required=True, states=STATES, depends=DEPENDS,
        help='The abstract title of the creation, needed to identify '
        'it later as a track within a release, for example.')
    artist = fields.Many2One(
        'artist', 'Artist', states=STATES, depends=DEPENDS, help='The named '
        'artist for the creation')
    lyrics = fields.Text(
        'Lyrics', help='The lyrics of the creation.')
    licenses = fields.Function(
        fields.Many2Many(
            'release.track', 'creation', 'license', 'Licenses'),
        'get_licenses')
    license = fields.Function(
        fields.Many2One('license', 'Default License'),
        'get_license', searcher='search_license')
    derivative_relations = fields.One2Many(
        'creation.original.derivative', 'original_creation',
        'Derived Relations', states=STATES, depends=DEPENDS,
        help='All creations deriving from the actual creation')
    original_relations = fields.One2Many(
        'creation.original.derivative', 'derivative_creation',
        'Originating Relations', states=STATES, depends=DEPENDS,
        help='All creations originating the actual creation')
    releases = fields.One2Many(
        'release.track', 'creation', 'Releases',
        help='The releases of this creation.')
    release = fields.Function(
        fields.Many2One('release', 'First Release'),
        'get_release', searcher='search_release')
    genres = fields.Function(
        fields.Many2Many(
            'release-genre', 'release', 'genre', 'Genres',
            help='Shows the collection of all genres of all releases'),
        'get_genres')
    styles = fields.Function(
        fields.Many2Many(
            'release-style', 'release', 'style', 'Styles',
            help='Shows the collection of all styles of all releases'),
        'get_styles', searcher='search_styles')
    content = fields.One2Many(
        'content', 'creation', 'Content',
        help='Content associated with the creation.')
    duration = fields.Function(
        fields.Float('Duration'),
        'get_duration')
    tariff_categories = fields.One2Many(
        'creation-tariff_category', 'creation', 'Tariff Category',
        help='Tariff categories of the creation.')
    tariff_categories_list = fields.Function(
        fields.Char('Tariff Category List'),
        'on_change_with_tariff_categories_list')
    cs_identifiers = fields.One2Many(
        'creation.cs_identifier', 'creation', '3rd-Party Identifier',)
    rights = fields.One2Many(
        'creation.right', 'rightsobject',
        'Creation Right', help='Creation Right')
    webiste_resources = fields.One2Many(
        'website.resource-creation', 'creation', 'resource'
        'Website Resource',
        help='The website resources, in which the creation was used')
    distribution_type_override = fields.Selection([
            (None, 'None'),
            *distribution_type_selection,
        ], 'Distribution Type', states={
            'invisible': Eval('distribution_type_override') is not None,
        }, help='The derivation type of the creation')
    distribution_type = fields.Function(
        fields.Selection(
            distribution_type_selection, 'Distribution Type',
            states={'invisible': Eval('distribution_type_override') is None}),
        'get_distribution_type', 'set_distribution_type')

    @fields.depends('tariff_categories')
    def on_change_with_tariff_categories_list(self, name=None):
        tariff_categories = ''
        for tariff_category in self.tariff_categories:
            tariff_categories += '%s, ' % tariff_category.category.code
        return tariff_categories.rstrip(', ')

    def get_rec_name(self, name):
        result = '[%s] %s' % (
            self.artist.name if self.artist and self.artist.name
            else '<unknown artist>',
            self.title)
        return result

    def get_licenses(self, name):
        licenses = []
        for releasecreation in self.releases:
            if releasecreation.license:
                licenses.append(releasecreation.license.id)
        return list(set(licenses))

    def get_license(self, name):
        license = None
        for lic in self.licenses:
            if not license or lic.freedom_rank > license.freedom_rank:
                license = lic
        return license and license.id or None

    def get_release(self, name):
        release = None
        earliest_date = None
        for releasecreation in self.releases:
            current_release = releasecreation.release
            online_date = current_release.online_release_date
            physical_date = current_release.release_date
            if not earliest_date:
                release = current_release
                if not online_date or physical_date < online_date:
                    earliest_date = physical_date
                else:
                    earliest_date = online_date
            if physical_date and physical_date < earliest_date:
                earliest_date = physical_date
                release = current_release
            if online_date and online_date < earliest_date:
                earliest_date = online_date
                release = current_release
        return release and release.id or None

    def get_genres(self, name):
        genres = []
        for releasecreation in self.releases:
            for genre in releasecreation.release.genres:
                if genre.id not in genres:
                    genres.append(genre.id)
        return genres

    def get_styles(self, name):
        styles = []
        for releasecreation in self.releases:
            for style in releasecreation.release.styles:
                if style.id not in styles:
                    styles.append(style.id)
        return styles

    def get_duration(self, name):
        for content in self.content:
            if content.category == "audio" and content.length:
                return content.length
        return None

    @classmethod
    def search_license(cls, name, clause):
        return [('license.' + clause[0],) + tuple(clause[1:])]

    @classmethod
    def search_release(cls, name, clause):
        return [('release.' + clause[0],) + tuple(clause[1:])]

    @classmethod
    def search_genres(cls, name, clause):
        return [('release-genre.' + clause[0],) + tuple(clause[1:])]

    @classmethod
    def search_styles(cls, name, clause):
        return [('release-style.' + clause[0],) + tuple(clause[1:])]

    @classmethod
    def create(cls, vlist):
        default_roles = [('add', [
            r.id for r in
            AccessRole.search([('name', 'in', DEFAULT_ACCESS_ROLES)])])]

        acls = {}
        elist = super().create(vlist)
        for entry in elist:
            if entry.acl:
                continue
            # always autocreate creator acl
            if entry.entity_creator and entry.entity_creator.web_user:
                acls[entry.entity_creator.web_user.id] = {
                    'entity': str(entry),
                    'web_user': entry.entity_creator.web_user.id,
                    'roles': default_roles
                }
        AccessControlEntry.create(list(acls.values()))

        return elist

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            'OR',
            ('code',) + tuple(clause[1:]),
            ('title',) + tuple(clause[1:]),
        ]

    @staticmethod
    def default_distribution_type_override():
        return 'original'

    def get_distribution_type(self, name):
        if self.distribution_type_override:
            return self.distribution_type_override
        if not self.original_relations:
            return 'original'
        originals = self.original_relations
        if len(originals) == 1:
            allocation_type = self.original_relations[0].allocation_type
            if allocation_type == "cover":
                return 'cover'
            if allocation_type == "adaption":
                return 'adaption'
        else:
            if all(original.allocation_type == "remix"
                   for original in originals):
                return "remix"
        raise f"Can't derive the distribution type from creation: {self}"

    @classmethod
    def set_distribution_type(cls, creations, name, value):
        for creation in creations:
            creation.distribution_type_override = value
            creation.save()

    def get_rights(self, right_type, contribution=None):
        if contribution:
            return [
                right for right in self.rights
                if right.type_of_right == right_type
                and right.contribution == contribution
            ]
        return [
            right for right in self.rights
            if right.type_of_right == right_type
        ]

    def get_rightsholders(self, right_type, contribution):
        return [
            right.rightsholder for right in self.rights
            if right.type_of_right == right_type
            and right.contribution == contribution
        ]

    def permits(self, web_user, code, derive=True):
        if super().permits(web_user, code, derive):
            return True
        if not derive:
            return False
        derivation = {
            'view_creation':   'view_artist_creations',
            'edit_creation':   'edit_artist_creations',
            'delete_creation': 'delete_artist_creations',
        }
        if self.artist:
            for ace in self.artist.acl:
                if ace.web_user != web_user:
                    continue
                for role in ace.roles:
                    for permission in role.permissions:
                        if permission.code == derivation[code]:
                            return True
        return False

    def permissions(self, web_user, valid_codes=[], derive=True):
        direct_permissions = super().permissions(
            web_user, valid_codes, derive)
        if not derive:
            return direct_permissions
        derivation = {
            'view_artist_creations':   'view_creation',
            'edit_artist_creations':   'edit_creation',
            'delete_artist_creations': 'delete_creation',
        }
        if not set(valid_codes).intersection(set(derivation.values())):
            return direct_permissions
        permissions = set(direct_permissions)
        if self.artist:
            for ace in self.artist.acl:
                if not derivation:
                    continue
                if ace.web_user != web_user:
                    continue
                for role in ace.roles:
                    for permission in role.permissions:
                        if permission.code in derivation:
                            permissions.add(derivation[permission.code])
                            del derivation[permission.code]
            if valid_codes:
                permissions = permissions.intersection(valid_codes)
        return tuple(permissions)


class CreationDerivative(PublicApi, ModelSQL, ModelView):
    'Creation - Original - Derivative'
    __name__ = 'creation.original.derivative'
    _history = True

    original_creation = fields.Many2One(
        'creation', 'Original Creation', required=True,
        ondelete='CASCADE')
    derivative_creation = fields.Many2One(
        'creation', 'Derivative Creation', required=True,
        ondelete='CASCADE')
    allocation_type = fields.Selection(
        [
            (None, ''),
            ('adaption', 'Adaption'),
            ('cover', 'Cover'),
            ('remix', 'Remix'),
        ], 'Allocation Type', sort=False,
        help='The allocation type of the actual creation in the relation '
        'from its origins or towards its derivatives\n'
        '*Adaption*: \n'
        '*Cover*: \n'
        '*Remix*: \n')


class CreationRole(PublicApi, ModelSQL, ModelView, EntityOrigin):
    'Creation Role'
    __name__ = 'creation.role'
    _history = True

    name = fields.Char(
        'Name', required=True, translate=True, help='The name of the role')
    description = fields.Text(
        'Description', translate=True, help='The description of the role')


class CreationTariffCategory(PublicApi, ModelSQL, ModelView):
    'Creation - Tariff Category'
    __name__ = 'creation-tariff_category'
    _history = True

    creation = fields.Many2One(
        'creation', 'Creation', required=True, ondelete='CASCADE')
    category = fields.Many2One(
        'tariff_system.category', 'Category', required=True,
        ondelete='CASCADE')

    collecting_society = fields.Many2One(
        'collecting_society', 'Collecting Society', ondelete='CASCADE')


class CreationIdentifier(ModelSQL, ModelView, MixinIdentifier):
    'Creation Identifier'
    __name__ = 'creation.cs_identifier'
    _history = True
    space = fields.Many2One(
        'creation.cs_identifier.space', 'Creation Identifier Space',
        required=True, ondelete='CASCADE')
    creation = fields.Many2One(
        'creation', 'Creation',
        required=True, ondelete='CASCADE')


class CreationIdentifierSpace(ModelSQL, ModelView):
    'Creation Identifier Space'
    __name__ = 'creation.cs_identifier.space'
    _history = True
    name = fields.Char('Name of the ID space')
    version = fields.Char('Version')


class CreationRight(PublicApi, ModelSQL, ModelView, MixinRight):
    'Creation Rights'
    __name__ = 'creation.right'
    _history = True

    rightsholder = fields.Many2One(
        'party.party', 'Rightsholder', required=True, ondelete='CASCADE')
    rightsobject = fields.Many2One(
        'creation', 'Creation', required=True, ondelete='CASCADE')
    contribution = fields.Selection(
        'get_contribution', 'Contribution Type')
    successor = fields.One2One(
        'creation.right-creation.right', 'predecessor',
        'successor', 'Successor', help='Successor')
    predecessor = fields.One2One(
        'creation.right-creation.right', 'successor',
        'predecessor', 'Predecessor', help='Predecessor')
    instruments = fields.Many2Many(
        'creation.right-instrument', 'right', 'instrument',
        'Instruments',
        states={
            'required': Eval('contribution') == 'instrument',
            'invisible': Eval('contribution') != 'instrument'
        }, depends=['contribution'],
        help='Instrument the rightsholder performed with')

    @fields.depends('type_of_right')
    def get_contribution(self):
        if self.type_of_right == 'copyright':
            return [
                ('lyrics', 'Lyrics'),
                ('composition', 'Composition'),
            ]
        elif self.type_of_right == 'ancillary':
            return [
                ('instrument', 'Instrument'),
                ('production', 'Production'),
                ('mixing', 'Mixing'),
                ('mastering', 'Mastering'),
            ]
        return list()


class CreationRightCreationRight(ModelSQL):
    'CreationRight - CreationRight'
    __name__ = 'creation.right-creation.right'
    _history = True

    predecessor = fields.Many2One(
        'creation.right', 'Predecessor', required=True, ondelete='CASCADE')
    successor = fields.Many2One(
        'creation.right', 'Successor', required=True, ondelete='CASCADE')


class Release(CodeSequence, PublicApi, ModelSQL, ModelView, EntityOrigin,
              AccessControlList, CurrentState, MixinIdentifierHelper,
              ClaimState, CommitState, metaclass=IndicatorsMeta):
    'Release'
    __name__ = 'release'
    _history = True
    _rec_name = 'title'
    _code_sequence = 'release_sequence'

    # Note: The metaclass adds relations to indicators and shortcut function
    #       fields to their attributes to this class (see metaclass docstring)
    __indicators__ = 'release.indicators'
    __samples__ = ['confirmed']

    type = fields.Selection(
        [
            ('artist', 'Artist Release'),
            ('split', 'Split Release'),
            ('compilation', 'Compilation'),
        ], 'Release Type', required=True, help='The release type:\n\n'
        '*Artist Release*: The release belongs to one or more artists '
        '(artist/split album).\n'
        '*Compilation*: The release belongs to the producer of the '
        'compilation and usually contains various artists.')

    # artists
    artists = fields.Many2Many(
        'artist-release', 'release', 'artist', 'Artists',
        help='The artists, to which the release belongs.',
        states={
            'required': Eval('type') == 'artist',
            'invisible': Eval('type') != 'artist',
        }, depends=['type'])
    artists_list = fields.Function(
        fields.Char('Artists List'), 'on_change_with_artists_list')

    # tracks
    tracks = fields.One2Many(
        'release.track', 'release', 'Creations',
        help='The tracks of the release')
    # medium_numbers = fields.Function(
    #     fields.Many2Many(
    #         'release.track', 'creation', 'release', 'Media Numbers',
    #         help='Media numbers of the Release.'),
    #     'get_medium_numbers')

    # metadata
    title = fields.Char('Title')
    picture_data = fields.Binary(
        'Picture Data', states=STATES, depends=DEPENDS,
        help='Picture data of a photograph or logo')
    picture_data_md5 = fields.Char(
        'Picture Data Hash', states=STATES, depends=DEPENDS,
        help='The md5 hash of the picture data, also acting as ressouce name.')
    picture_thumbnail_data = fields.Binary(
        'Thumbnail Data', states=STATES, depends=DEPENDS,
        help='Thumbnail data of the picture')
    picture_data_mime_type = fields.Char(
        'Picture Data Mime Type', states=STATES, depends=DEPENDS,
        help='The mime type of picture data.')
    genres = fields.Many2Many(
        'release-genre', 'release', 'genre', 'Genres',
        help='The genres of the release.')
    styles = fields.Many2Many(
        'release-style', 'release', 'style', 'Styles',
        help='The styles of the release.')
    warning = fields.Char(
        'Warning', help='A warning note for this release.')

    # production
    copyright_date = fields.Date(
        'Copyright Date', help='Date of the copyright.')
    production_date = fields.Date(
        'Production Date', help='Date of production.')
    # producers = fields.Function(
    #     fields.Many2Many(
    #         'creation.contribution', 'creation', 'artist', 'Producer(s)',
    #         help='Producers involved in the creations of the release.'),
    #     'get_producers')

    # distribution
    release_date = fields.Date('Release Date', help='Date of (first) release.')
    release_cancellation_date = fields.Date(
        'Release Cancellation Date', help='Date of release cancellation')
    online_release_date = fields.Date(
        'Online Release Date', help='The Date of digital online release.')
    online_cancellation_date = fields.Date(
        'Online Cancellation Date',
        help='Date of online release cancellation.')
    distribution_territory = fields.Char(
        'Distribution Territory')
    label = fields.Many2One(
        'label', 'Label', help='The label of the release.')
    label_catalog_number = fields.Char(
        'Label Catalog Number',
        help='The labels catalog number of the release.')
    publisher = fields.Many2One(
        'publisher', 'Publisher', help='The publisher of the release.')
    # neighbouring_rights_societies = fields.Function(
    #     fields.Many2Many(
    #        'collecting_society', None, None, 'Neighbouring Rights Societies',
    #        help='Neighbouring Rights Societies involved in the creations of '
    #         'the release.'),
    #     'get_neighbouring_rights_societies')
    cs_identifiers = fields.One2Many(
        'release.cs_identifier', 'release', '3rd-party identifier',)
    rights = fields.One2Many(
        'release.right', 'rightsobject', 'Release Right',
        help='Release Right')
    published = fields.Boolean(
        'Published', help='Is the release published and publicly accessible?')

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._order.insert(1, ('title', 'ASC'))

    @classmethod
    def create(cls, vlist):
        default_roles = [('add', [
            r.id for r in
            AccessRole.search([('name', 'in', DEFAULT_ACCESS_ROLES)])])]

        acls = {}
        elist = super().create(vlist)
        for entry in elist:
            if entry.acl:
                continue
            # always autocreate creator acl
            if entry.entity_creator and entry.entity_creator.web_user:
                acls[entry.entity_creator.web_user.id] = {
                    'entity': str(entry),
                    'web_user': entry.entity_creator.web_user.id,
                    'roles': default_roles
                }
        AccessControlEntry.create(list(acls.values()))

        return elist

    @classmethod
    def delete(cls, records):
        for record in records:
            if record.genres:
                record.genres = []
                record.save()
        return super().delete(records)

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            'OR',
            ('code',) + tuple(clause[1:]),
            ('title',) + tuple(clause[1:]),
        ]

    @fields.depends('artists')
    def on_change_with_artists_list(self, name=None):
        artists = []
        for artist in self.artists:
            artists.append(artist.name)
        return ", ".join(artists)

    # tried to get a nice ordered list of media
    # (see function field above)
    # def get_medium_numbers(self, name):
    #     medium_numbers = []
    #     for track in self.tracks:
    #             medium_numbers.append(track)
    #     return list(set(medium_numbers))

    # def get_producers(self, name):
    #     producers = []
    #     for track in self.tracks:
    #         for contribution in track.creation.contributions:
    #             performance = (contribution.type == 'performance')
    #             producing = (contribution.performance == 'producing')
    #             if performance and producing:
    #                 producers.append(contribution.artist.id)
    #     return list(set(producers))

    # def get_neighbouring_rights_societies(self, name):
    #     societies = []
    #     for track in self.tracks:
    #         for contribution in track.creation.contributions:
    #             performance = (contribution.type == 'performance')
    #             society = contribution.neighbouring_rights_society
    #             if performance and society:
    #                 societies.append(society.id)
    #     return list(set(societies))

    def permits(self, web_user, code, derive=True):
        if super().permits(web_user, code, derive):
            return True
        if not derive:
            return False
        derivation = {
            'view_release':   'view_artist_releases',
            'edit_release':   'edit_artist_releases',
            'delete_release': 'delete_artist_releases',
        }
        for artist in self.artists:
            for ace in artist.acl:
                if ace.web_user != web_user:
                    continue
                for role in ace.roles:
                    for permission in role.permissions:
                        if permission.code == derivation[code]:
                            return True
        return False

    def permissions(self, web_user, valid_codes=[], derive=True):
        direct_permissions = super().permissions(
            web_user, valid_codes, derive)
        if not derive:
            return direct_permissions
        derivation = {
            'view_artist_releases':   'view_release',
            'edit_artist_releases':   'edit_release',
            'delete_artist_releases': 'delete_release',
        }
        if not set(valid_codes).intersection(set(derivation.values())):
            return direct_permissions
        permissions = set(direct_permissions)
        for artist in self.artists:
            for ace in artist.acl:
                if not derivation:
                    continue
                if ace.web_user != web_user:
                    continue
                for role in ace.roles:
                    for permission in role.permissions:
                        if permission.code in derivation:
                            permissions.add(derivation[permission.code])
                            del derivation[permission.code]
            if valid_codes:
                permissions = permissions.intersection(valid_codes)
        return tuple(permissions)


class ReleaseTrack(ModelSQL, ModelView, PublicApi):
    'Release Track'
    __name__ = 'release.track'
    _history = True

    release = fields.Many2One(
        'release', 'Release', required=True, ondelete='CASCADE')
    creation = fields.Many2One(
        'creation', 'Creation', required=True, ondelete='CASCADE')

    title = fields.Char(
        'Title', states={'required': True},
        help='The title or name of the creation on the release')
    medium_number = fields.Integer(
        'Medium Number', help='The number of the medium on CD, LP, ...')
    track_number = fields.Integer(
        'Track Number', help='Track number on the medium')
    license = fields.Many2One(
        'license', 'License', help='License for the creation on the release')


class ReleaseGenre(ModelSQL, ModelView):
    'Release - Genre'
    __name__ = 'release-genre'
    _history = True

    release = fields.Many2One(
        'release', 'Release', required=True, ondelete='CASCADE')
    genre = fields.Many2One(
        'genre', 'Genre', required=True, ondelete='CASCADE')


class ReleaseStyle(ModelSQL, ModelView):
    'Release - Style'
    __name__ = 'release-style'
    _history = True

    release = fields.Many2One(
        'release', 'Release', required=True, ondelete='CASCADE')
    style = fields.Many2One(
        'style', 'Style', required=True, ondelete='CASCADE')


class ReleaseIdentifier(ModelSQL, ModelView, MixinIdentifier):
    'Release Identifier'
    __name__ = 'release.cs_identifier'
    _history = True
    space = fields.Many2One(
        'release.cs_identifier.space', 'Release Identifier Space',
        required=True, ondelete='CASCADE')
    release = fields.Many2One(
        'release', 'Release', required=True, ondelete='CASCADE')


class ReleaseIdentifierSpace(ModelSQL, ModelView):
    'Release Identifier Space'
    __name__ = 'release.cs_identifier.space'
    _history = True
    name = fields.Char('Name of the ID space')
    version = fields.Char('Version')


class ReleaseRight(ModelSQL, ModelView, MixinRight):
    'Release Right'
    __name__ = 'release.right'
    _history = True
    rightsholder = fields.Many2One(
        'party.party', 'Rightsholder', required=True, ondelete='CASCADE')
    rightsobject = fields.Many2One(
        'release', 'Release', required=True, ondelete='CASCADE')
    contribution = fields.Function(
        fields.Char('Contribution Right'),
        'get_contribution')
    successor = fields.One2One(
        'release.right-release.right', 'predecessor',
        'successor', 'Successor', help='Successor')
    predecessor = fields.One2One(
        'release.right-release.right', 'successor',
        'predecessor', 'Predecessor', help='Predecessor')

    @fields.depends('type_of_right')
    def get_contribution(self):
        if self.type_of_right == 'copyright':
            return ('Artwork', 'Text', 'Layout')
        elif self.type_of_right == 'ancillary':
            return ('Production', 'Mixing', 'Mastering')


class ReleaseRightReleaseRight(ModelSQL):
    'ReleaseRight - ReleaseRight'
    __name__ = 'release.right-release.right'
    _history = True

    predecessor = fields.Many2One(
        'release.right', 'Predecessor', required=True,
        ondelete='CASCADE')
    successor = fields.Many2One(
        'release.right', 'Successor', required=True,
        ondelete='CASCADE')


class Instrument(PublicApi, ModelSQL, ModelView):
    'Instrument'
    __name__ = 'instrument'
    _history = True

    name = fields.Char(
        'Name', help='The name of the instrument.')
    description = fields.Text(
        'Description', help='The description of the instrument.')


class CreationRightInstrument(ModelSQL):
    'CreationRightInstrument'
    __name__ = 'creation.right-instrument'
    _history = True

    right = fields.Many2One(
        'creation.right', 'Right', required=True,
        ondelete='CASCADE')
    instrument = fields.Many2One(
        'instrument', 'Instrument', required=True,
        ondelete='CASCADE')


class Genre(PublicApi, ModelSQL, ModelView):
    'Genre'
    __name__ = 'genre'
    _history = True

    name = fields.Char('Name', help='The name of the genre.')
    description = fields.Text(
        'Description', help='The description of the genre.')


class Style(PublicApi, ModelSQL, ModelView):
    'Style'
    __name__ = 'style'
    _history = True

    name = fields.Char('Name', help='The name of the style.')
    description = fields.Text(
        'Description', help='The description of the style.')


class Label(PublicApi, ModelSQL, ModelView, EntityOrigin, CurrentState):
    'Label'
    __name__ = 'label'
    _history = True

    name = fields.Char('Name', help='The name of the label.')
    party = fields.Many2One(
        'party.party', 'Party', help='The legal party of the label')
    gvl_code = fields.Char(
        'GVL Code', help='The label code of the german '
        '"Gesellschaft zur Verwertung von Leistungsschutzrechten" (GVL)')


class Publisher(PublicApi, ModelSQL, ModelView, EntityOrigin, CurrentState):
    'Publisher'
    __name__ = 'publisher'
    _history = True

    name = fields.Char('Name', help='The name of the publisher.')
    party = fields.Many2One(
        'party.party', 'Party', help='The legal party of the publisher')


##############################################################################
# Licensee
##############################################################################

# --- Real World Objects -----------------------------------------------------

class Event(PublicApi, ModelSQL, ModelView, CurrencyDigits, CurrentState,
            metaclass=IndicatorsMeta):
    'Event'
    __name__ = 'event'
    _history = True

    # Note: The metaclass adds relations to indicators and shortcut function
    #       fields to their attributes to this class (see metaclass docstring)
    __indicators__ = 'event.indicators'
    __samples__ = ['estimated', 'confirmed']

    name = fields.Char(
        'Name', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The name of the event')
    description = fields.Text(
        'Description', states=STATES, depends=DEPENDS,
        help='A description of the event.')

    location = fields.Many2One(
        'location', 'Location', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The location of the event')
    performances = fields.One2Many(
        'event.performance', 'event', 'Performances',
        states=STATES, depends=DEPENDS,
        help='The performences of the event')

    # shortcuts to attributes in indicators
    start = fields.Function(
        fields.DateTime(
            'Start', help='Start of the event'),
        'get_start')
    end = fields.Function(
        fields.DateTime(
            'End', help='End of the event'),
        'get_end')

    def get_start(self, name=None):
        if self.confirmed_indicators and self.confirmed_indicators.start:
            return self.confirmed_indicators.start
        if self.estimated_indicators and self.estimated_indicators.start:
            return self.estimated_indicators.start
        return None

    def get_end(self, name=None):
        if self.confirmed_indicators and self.confirmed_indicators.end:
            return self.confirmed_indicators.end
        if self.estimated_indicators and self.estimated_indicators.end:
            return self.estimated_indicators.end
        return None


class EventPerformance(PublicApi, ModelSQL, ModelView, CurrentState):
    'Event Performance'
    __name__ = 'event.performance'
    _history = True

    start = fields.DateTime(
        'Start', states=STATES, depends=DEPENDS,
        help='Start of the performance')
    end = fields.DateTime(
        'End', states=STATES, depends=DEPENDS,
        help='End of the performance')
    event = fields.Many2One(
        'event', 'Event', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS, ondelete='CASCADE',
        help='The event of the performance')
    artist = fields.Many2One(
        'artist', 'Artist', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The artist of the performance')
    playlist = fields.Many2One(
        'artist.playlist', 'Playlist',
        states=STATES, depends=['active', 'artist'],
        domain=[('artist', '=', Eval('artist'))],
        help='The playlist of the performance')


class Location(PublicApi, ModelSQL, ModelView, CurrencyDigits, CurrentState,
               ClaimState, EntityOrigin, metaclass=IndicatorsMeta):
    'Location'
    __name__ = 'location'
    _history = True

    # Note: The metaclass adds relations to indicators and shortcut function
    #       fields to their attributes to this class (see metaclass docstring)
    __indicators__ = 'location.indicators'
    __samples__ = ['estimated', 'confirmed']

    name = fields.Char(
        'Name', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The name of the location')
    category = fields.Many2One(
        'location.category', 'Category', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The category of the location')
    party = fields.Many2One(
        'party.party', 'Party', states={
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The party responsible for the location')

    public = fields.Boolean(
        'Public', states=STATES, depends=DEPENDS,
        help='Visibility for other frontend users')

    street = fields.Text("Street")
    postal_code = fields.Char("Postal Code")
    city = fields.Char("City")
    country = fields.Many2One('country.country', "Country")
    latitude = fields.Float(
        'Latitude', states=STATES, depends=DEPENDS,
        help='The latitude of the geographical location')
    longitude = fields.Float(
        'Longitude', states=STATES, depends=DEPENDS,
        help='The longitude of the geographical location')

    spaces = fields.One2Many(
        'location.space', 'location', 'Spaces',
        states=STATES, depends=DEPENDS,
        help='The spaces associated with the location')


class LocationCategory(Code, PublicApi, ModelSQL, ModelView, CurrentState):
    'Location Category'
    __name__ = 'location.category'
    _history = True

    name = fields.Char(
        'Name', required=True, states=STATES, depends=DEPENDS,
        help="The name of the location category")
    description = fields.Text(
        'Description', states=STATES, depends=DEPENDS,
        help='A description of the location category.')

    locations = fields.One2Many(
        'location', 'category', 'Locations',
        states=STATES, depends=DEPENDS,
        help='The locations within the category')

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            'OR',
            ('name',) + tuple(clause[1:]),
            ('code',) + tuple(clause[1:]),
        ]


class LocationSpace(PublicApi, ModelSQL, ModelView, CurrentState,
                    metaclass=IndicatorsMeta):
    'Location Space'
    __name__ = 'location.space'
    _history = True

    # Note: The metaclass adds relations to indicators and shortcut function
    #       fields to their attributes to this class (see metaclass docstring)
    __indicators__ = 'location.space.indicators'
    __samples__ = ['estimated', 'confirmed']

    name = fields.Char(
        'Name', required=False, states=STATES, depends=DEPENDS,
        help="The name of the location space")
    location = fields.Many2One(
        'location', 'Location', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The location of the location space')
    # events = fields.One2Many(
    #     'event', 'location', 'Events', states=STATES, depends=DEPENDS,
    #     help='The events in the location')
    category = fields.Many2One(
        'location.space.category', 'Category', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The category of the location space')

    device_assignments = fields.One2Many(
        'device.assignment', 'assignment', 'Device Assignments',
        states=STATES, depends=DEPENDS,
        help='The assigned devices')
    current_devices = fields.Function(
        fields.One2Many(
            'device', None, 'Current Devices',
            help="The currently associated devices"),
        'get_current_devices')
    messages = fields.One2Many(
        'device.message', 'context', 'Messages',
        states=STATES, depends=DEPENDS,
        help='The device messages for the location space')
    fingerprints = fields.Function(
        fields.One2Many(
            'device.message.fingerprint', None, 'Fingerprints'),
        'get_fingerprints')

    playlists = fields.One2Many(
        'utilisation.creationlist', 'context', 'Utilisation Creationlists',
        states=STATES, depends=DEPENDS,
        help='The utilisation creation lists of the location space')

    # shortcuts to attributes in indicators
    size = fields.Function(
        fields.Integer(
            'Size', help='The size of the location space [squaremeter]'),
        'get_size')

    def get_size(self, name=None):
        if self.confirmed_indicators and self.confirmed_indicators.size:
            return self.confirmed_indicators.size
        if self.estimated_indicators and self.estimated_indicators.size:
            return self.estimated_indicators.size
        return None

    def get_current_devices(self, name=None):
        devices = []
        now = datetime.datetime.now()
        for assignment in self.device_assignments:
            if not assignment.start or assignment.start > now:
                continue
            if assignment.end and assignment.end < now:
                continue
            devices.append(assignment.device.id)
        return devices

    def get_message_content(self, category):
        contents = []
        for message in self.messages:
            if message.category == category and message.content:
                contents.append(message.content.id)
        return contents

    def get_fingerprints(self, name):
        return self.get_message_content('fingerprint')


class LocationSpaceCategory(Code, PublicApi, ModelSQL, ModelView,
                            CurrentState):
    'Location Space Category'
    __name__ = 'location.space.category'
    _history = True

    name = fields.Char(
        'Name', required=True, states=STATES, depends=DEPENDS,
        help="The name of the location space category")
    description = fields.Text(
        'Description', states=STATES, depends=DEPENDS,
        help='A description of the location space category.')

    spaces = fields.One2Many(
        'location.space', 'category', 'Spaces', states=STATES, depends=DEPENDS,
        help='The location spaces within the category')

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            'OR',
            ('name',) + tuple(clause[1:]),
            ('code',) + tuple(clause[1:]),
        ]


class Website(PublicApi, ModelSQL, ModelView, CurrentState):
    'Website'
    __name__ = 'website'
    _history = True

    name = fields.Char(
        'Name', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The name of the location')
    category = fields.Many2One(
        'website.category', 'Category', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The category of the website')
    party = fields.Many2One(
        'party.party', 'Party', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The party responsible for the website')
    url = fields.Char(
        'URL', states=STATES, depends=DEPENDS, help='The url of the website')

    website_resources = fields.One2Many(
        'website.resource', 'website', 'Resources',
        states=STATES, depends=DEPENDS,
        help='The resources of the website')

    device_assignments = fields.One2Many(
        'device.assignment', 'assignment', 'Device Assignments',
        states=STATES, depends=DEPENDS,
        help='The assigned devices')
    current_devices = fields.Function(
        fields.One2Many(
            'device', None, 'Current Devices',
            help="The currently associated devices"),
        'get_current_devices')

    def get_current_devices(self, name=None):
        devices = []
        now = datetime.datetime.now()
        for assignment in self.device_assignments:
            if not assignment.start or assignment.start > now:
                continue
            if assignment.end and assignment.end < now:
                continue
            devices.append(assignment.device.id)
        return devices


class WebsiteCategory(Code, PublicApi, ModelSQL, ModelView, CurrentState):
    'Website Category'
    __name__ = 'website.category'
    _history = True

    name = fields.Char(
        'Name', required=True, states=STATES, depends=DEPENDS,
        help='The name of the website category')
    description = fields.Text(
        'Description', states=STATES, depends=DEPENDS,
        help='A description of the website category.')

    resource_categories = fields.Many2Many(
        'website.category-website.resource.category',
        'website_category', 'website_resource_category',
        'Website Resource Categories',
        states=STATES, depends=DEPENDS,
        help='The website resource categories applicable for the website '
             'category')

    websites = fields.One2Many(
        'website', 'category', 'Websites', states=STATES, depends=DEPENDS,
        help='The websites within the category')

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            'OR',
            ('name',) + tuple(clause[1:]),
            ('code',) + tuple(clause[1:]),
        ]


class WebsiteResource(UUID, PublicApi, ModelSQL, ModelView, CurrencyDigits,
                      CurrentState):
    'Website Resource'
    __name__ = 'website.resource'
    _history = True

    name = fields.Char(
        'Name', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The name of the resource')
    website = fields.Many2One(
        'website', 'Website', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The website of the resource')
    category = fields.Many2One(
        'website.resource.category', 'Category', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        # TODO: only selection of website resource cats valid for website cat
        # domain=[('website_categories.code', '=', 'website.category.code')],
        # domain=[('code', '=', 'website.category.resource_categories.code')],
        help='The category of the resource')

    url = fields.Char(
        'URL', states=STATES, depends=DEPENDS, help='The url of the website')
    messages = fields.One2Many(
        'device.message', 'context', 'Messages',
        states=STATES, depends=DEPENDS,
        help='The device messages for the website resource')
    usagereports = fields.Function(
        fields.One2Many(
            'device.message.usagereport', None, 'Usage Reports'),
        'get_usagereports')
    fingerprints = fields.Function(
        fields.One2Many(
            'device.message.fingerprint', None, 'Fingerprints'),
        'get_fingerprints')

    originals = fields.Many2Many(
        'website.resource-creation', 'resource', 'creation', 'Originals',
        states=STATES, depends=DEPENDS,
        help='The originals used in the resource')
    playlists = fields.One2Many(
        'utilisation.creationlist', 'context', 'Utilisation Creationlists',
        states=STATES, depends=DEPENDS,
        help='The utilisation creation lists of the website resource')

    def get_message_content(self, category):
        contents = []
        for message in self.messages:
            if message.category == category:
                contents.append(message.content.id)
        return contents

    def get_usagereports(self, name):
        return self.get_message_content('usagereport')

    def get_fingerprints(self, name):
        return self.get_message_content('fingerprint')


class WebsiteResourceCreation(ModelSQL):
    'Website Resource'
    __name__ = 'website.resource-creation'
    _history = True

    resource = fields.Many2One(
        'website.resource', 'Resource', required=True,
        ondelete='CASCADE')
    creation = fields.Many2One(
        'creation', 'Creation', required=True,
        ondelete='CASCADE')


class WebsiteResourceCategory(Code, PublicApi, ModelSQL, ModelView,
                              CurrentState):
    'Website Resource Category'
    __name__ = 'website.resource.category'
    _history = True

    name = fields.Char(
        'Name', required=True, states=STATES, depends=DEPENDS,
        help='The name of the resource category')
    description = fields.Text(
        'Description', states=STATES, depends=DEPENDS,
        help='A description of the resource category.')

    website_categories = fields.Many2Many(
        'website.category-website.resource.category',
        'website_resource_category', 'website_category',
        'Website Categories', states=STATES, depends=DEPENDS,
        help='The website categories for which the website resource category '
             'is applicable')

    website_resources = fields.One2Many(
        'website.resource', 'category', 'Resources',
        states=STATES, depends=DEPENDS,
        help='The resources within the category')

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            'OR',
            ('name',) + tuple(clause[1:]),
            ('code',) + tuple(clause[1:]),
        ]


class WebsiteCategoryWebsiteResourceCategory(ModelSQL):
    'Website Resource Category'
    __name__ = 'website.category-website.resource.category'
    _history = True

    website_category = fields.Many2One(
        'website.category', 'Website Category',
        required=True, ondelete='CASCADE')
    website_resource_category = fields.Many2One(
        'website.resource.category', 'Website Resource Category',
        required=True, ondelete='CASCADE')


# --- Devices ----------------------------------------------------------------

class Device(UUID, PublicApi, ModelSQL, ModelView, CurrentState):
    'Device'
    __name__ = 'device'
    _history = True
    _rec_name = 'uuid'

    web_user = fields.Many2One(
        'web.user', 'Web User', required=True, states=STATES, depends=DEPENDS,
        help='The web user of the device')
    blocked = fields.Boolean(
        'Blocked', states=STATES, depends=DEPENDS,
        help='The blocked state of the device.')

    assignments = fields.One2Many(
        'device.assignment', 'device', 'Assignments',
        states=STATES, depends=DEPENDS,
        help='The assigned objects of the device')
    messages = fields.One2Many(
        'device.message', 'device', 'Messages',
        states=STATES, depends=DEPENDS,
        help='The messages belonging to the device')

    name = fields.Char(
        'Device Name', states=STATES, depends=DEPENDS,
        help='Name of the device, i.e. model name, etc.')
    os_name = fields.Char(
        'OS Name', states=STATES, depends=DEPENDS,
        help='Name of the OS the device runs on')
    os_version = fields.Char(
        'OS Version', states=STATES, depends=DEPENDS,
        help='Version of the OS the device runs on')
    software_name = fields.Char(
        'Software Name', states=STATES, depends=DEPENDS,
        help='Name of the software on the device')
    software_version = fields.Char(
        'Software Version', states=STATES, depends=DEPENDS,
        help='The version of the software on the device')
    software_vendor = fields.Char(
        'Software Vendor', states=STATES, depends=DEPENDS,
        help='Vendor of the software on the device')


class DeviceAssignment(ModelSQL, ModelView):
    'Device Assignment'
    __name__ = 'device.assignment'
    _history = True
    device = fields.Many2One(
        'device', 'Device', required=True, help='The assigned device')
    assignment = fields.Reference(
        'Assignment', [
            ('location.space', 'Location Space'),
            ('website', 'Website'),
        ],
        help='The object the device is assigned to')
    start = fields.DateTime(
        'Start', states={'required': True},
        help='Start time of the assignment')
    end = fields.DateTime(
        'End', help='End time of the assignment')


class DeviceMessage(UUID, ModelSQL, ModelView):
    'Device Message'
    __name__ = 'device.message'
    _history = True

    device = fields.Many2One(
        'device', 'Device', states={'required': True},
        help='The device of the message')

    timestamp = fields.DateTime(
        'Timestamp', states={'required': True},
        help='The point in time, when the message arrived or was sent.')
    direction = fields.Selection(
        [
            ('incoming', 'Incoming'),
            ('outgoing', 'Outgoing'),
        ], 'Direction', sort=False, states={'required': True},
        help='The direction of the message: Incoming or Outgoing')
    category = fields.Selection(
        [
            ('fingerprint', 'Fingerprint'),
            ('usagereport', 'Usage Report'),
        ], 'Category', sort=False, states={'required': True},
        help='The category of the message content: Incoming or Outgoing')

    previous_message = fields.One2One(
        'device.message-device.message', 'next_message', 'previous_message',
        'Previous Message', domain=[
            [
                'OR',
                # only free ones
                [('next_message', '=', None)],
                # allow saving (new relations to the current one)
                [('next_message.id', '=', Eval('id', -1))]
            ],
            # no circles
            ('last_message', '!=', Eval('last_message', -1)),
            # no self reference
            ('id', '!=', Eval('id', -1)),
        ], depends=['id', 'last_message'],
        help='The previous message in a message sequence')
    next_message = fields.One2One(
        'device.message-device.message', 'previous_message', 'next_message',
        'Next Message', domain=[
            ['OR',
                # only free ones
                [('previous_message', '=', None)],
                # allow saving (new relations to the current one)
                [('previous_message.id', '=', Eval('id', -1))]],
            # no circles
            ('first_message', '!=', Eval('first_message', -1)),
            # no self reference
            ('id', '!=', Eval('id', -1)),
        ], depends=['id', 'first_message'],
        help='The next message in a message sequence')
    first_message = fields.Function(
        fields.Many2One(
            'device.message', 'First Message', help='The first message'),
        'get_first_message', searcher='search_message_id')
    last_message = fields.Function(
        fields.Many2One(
            'device.message', 'Last Message', help='The last message'),
        'get_last_message', searcher='search_message_id')

    context = fields.Reference(
        'Context', [
            ('location.space', 'Location Space'),
            ('website.resource', 'Website Resource'),
        ], help='The object, which the message is referencing')
    content = fields.Reference(
        'Content', 'selection_content', help='The message content')

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            'OR',
            ('uuid',) + tuple(clause[1:]),
            ('timestamp',) + tuple(clause[1:]),
        ]

    @classmethod
    def search_message_id(cls, name, clause):
        return [
            ('id',) + tuple(clause[1:])
        ]

    @fields.depends('category')
    def selection_content(self):
        if self.category == 'fingerprint':
            return [('', ''), ('device.message.fingerprint', 'Fingerprint')]
        if self.category == 'usagereport':
            return [('', ''), ('device.message.usagereport', 'Usage Report')]
        return [('', '')]

    def get_first_message(self, name=None):
        reentrance_message = self.previous_message
        message = self.previous_message
        while message:
            if not message.previous_message:
                return (message.id)
            message = message.previous_message
            if message == reentrance_message:
                raise Exception('Circular sequence detected: %s' % self)
        return None

    def get_last_message(self, name=None):
        reentrance_message = self.next_message
        message = self.next_message
        while message:
            if not message.next_message:
                return (message.id)
            message = message.next_message
            if message == reentrance_message:
                raise Exception('Circular sequence detected: %s' % self)
        return None


class DeviceMessageDeviceMessage(ModelSQL):
    'Device Message'
    __name__ = 'device.message-device.message'
    _history = True

    previous_message = fields.Many2One(
        'device.message', 'Previous Message', required=True,
        ondelete='CASCADE')
    next_message = fields.Many2One(
        'device.message', 'Next Message', required=True,
        ondelete='CASCADE')


fingerprint_states = [
    ('created', 'Created'),
    ('matched', 'Matched'),
    ('merged', 'Merged'),
    ('discarded', 'Discarded'),
]


class DeviceMessageFingerprint(ModelSQL, ModelView):
    'Device Message: Fingerprint'
    __name__ = 'device.message.fingerprint'
    _history = True

    device = fields.Function(
        fields.Many2One('device', 'Device'), 'get_device')
    # TODO: 2One interface via fields.Function
    message = fields.One2Many(
        'device.message', 'content', 'Message', states={'required': True},
        domain=[('category', '=', 'fingerprint')],
        help='The device message')
    state = fields.Selection(
        fingerprint_states, 'State', sort=False, states={'required': True},
        help='The state of the fingerprint:\n'
             '- Created: the fingerprint was created\n'
             '- Matched: a creation was tried to match\n'
             '- Merged: the matched creations were merged\n'
             '- Discarded: the fingerprint was discarded')
    matched_state = fields.Selection(
        [
            ('success', 'Success'),
            ('fail_score', 'Fail - Low Fingerprint Score'),
            ('fail_code', 'Fail - No Creation Code'),
            ('fail_creation', 'Fail - Creation Not Found'),
        ], 'Match', sort=False, states={
            'required': Eval('state') != 'created',
            'invisible': Eval('state') == 'created',
        }, depends=['state'], help='The state of the match:\n'
        '- Success: Match found.\n'
        '- Fail - Low Fingerprint Score: Fingerprint score too low.\n'
        '- Fail - No Creation Code: No creation code given.\n'
        '- Fail - Creation Not Found: No creation found.')
    matched_creation = fields.Many2One(
        'creation', 'Creation',
        help='The creation, which matches the fingerprint')
    merged_creation = fields.Many2One(
        'device.message.fingerprint.creationlist.item', 'Creation List Item',
        help='The item in the resulting creation list')

    timestamp = fields.DateTime(
        'Timestamp', states={'required': True},
        help='The point in time, when the creation was utlized')
    algorithm = fields.Char(
        'Algorithm', states={'required': True},
        help='The name of the fingerprinting algorithm')
    version = fields.Char(
        'Version', states={'required': True},
        help='The version of the fingerprinting algorithm')
    data = fields.Text(
        'Data', states={'required': True},
        help='The fingerprint data of a creation sample')

    def get_device(self, name):
        if self.message:
            return self.message[0].device.id


class DeviceMessageFingerprintMatchStart(ModelView):
    'Device Message Fingerprint Match Start'
    __name__ = 'device.message.fingerprint.match.start'
    fingerprints = fields.One2Many(
        'device.message.fingerprint', None, 'Fingerprints',
        states={'required': True}, help='The fingerprints to match')


class DeviceMessageFingerprintMatch(Wizard):
    'Device Message Fingerprint Match'
    __name__ = 'device.message.fingerprint.match'

    # TODO: Create a configuration model for fingerprint services
    fingerprint_services = {
        # algorithm
        'echoprint': {
            # version
            '1.0.0': {
                'url': '%s://%s:%s/query' % (
                    os.environ.get('ECHOPRINT_SCHEMA'),
                    os.environ.get('ECHOPRINT_HOSTNAME'),
                    os.environ.get('ECHOPRINT_PORT')),
                'data': lambda fingerprint: {
                    'fp_code': fingerprint.data.encode('utf8')
                },
                'verify': False,
                'threshold': 50
            }
        }
    }

    start = StateView(
        'device.message.fingerprint.match.start',
        'collecting_society.device_message_fingerprint_match_start_view_form',
        [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Match', 'match', 'tryton-ok', default=True),
        ])
    match = StateTransition()

    def default_start(self, fields):
        Fingerprint = Pool().get('device.message.fingerprint')
        active_model = Transaction().context.get('active_model', '')
        if active_model == 'device.message.fingerprint':
            fingerprints = Transaction().context['active_ids']
        else:
            fingerprints = [
                fingerprint.id for fingerprint
                in Fingerprint.search([('state', '=', 'created')])]
        return {
            'fingerprints': fingerprints
        }

    def transition_match(self):
        Warning = Pool().get('res.user.warning')
        Creation = Pool().get('creation')
        services = self.fingerprint_services
        for fingerprint in self.start.fingerprints:

            # sanity check: overwrite match
            if fingerprint.matched_creation:
                warning_name = 'matchalreadyexists,%s' % fingerprint.id
                if Warning.check(warning_name):
                    raise UserWarning(
                        warning_name, 'Match Already Exists',
                        'The fingerprint "%s" has already a matched creation '
                        '"%s", which might be overwritten if proceeded.' % (
                            fingerprint.id,
                            fingerprint.matched_creation.code))

            # sanity check: unkonwn algorithm
            if fingerprint.algorithm not in services:
                warning_name = 'unkownfingerprintalgorithm,%s' % fingerprint.id
                if Warning.check(warning_name):
                    raise UserWarning(
                        warning_name, 'Unkown Fingerprint Algorithm',
                        'The fingerprint "%s" cannot be matched, because the '
                        'algorithm "%s" is not known.' % (
                            fingerprint.id, fingerprint.algorithm))
                continue
            algorithm = services[fingerprint.algorithm]

            # sanity check: unkonwn version
            if fingerprint.version not in algorithm:
                warning_name = 'unkownfingerprintversion,%s' % fingerprint.id
                if Warning.check(warning_name):
                    raise UserWarning(
                        warning_name, 'Unkown Fingerprint Version',
                        'The fingerprint "%s" cannot be matched, because the '
                        'version "%s" for algorithm "%s" is not known.' % (
                            fingerprint.id, fingerprint.version,
                            fingerprint.algorithm))
                continue

            # sanity check: empty fingerprint data
            if not fingerprint.data:
                warning_name = 'nofingerprintdata,%s' % fingerprint.id
                if Warning.check(warning_name):
                    raise UserWarning(
                        warning_name, 'No Fingerprint Data',
                        'The fingerprint "%s" cannot be matched, because it '
                        'contains no data.' % fingerprint.id)
                continue

            # query fingerprint service
            service = algorithm[fingerprint.version]
            try:
                request = requests.post(
                    service['url'],
                    data=service['data'](fingerprint),
                    verify=service['verify']
                )
            except requests.exceptions.RequestException as e:
                raise UserError(
                    'Fingerprint Service Error',
                    'The service for algorithm "%s" version "%s" returned:\n\n'
                    '%s' % (
                        fingerprint.algorithm, fingerprint.version, e))

            # sanity check: response code
            if request.status_code != 200:
                warning_name = 'fingerprintserviceerror,%s' % hash(
                    fingerprint.algorithm + fingerprint.version)
                if Warning.check(warning_name):
                    raise UserWarning(
                        warning_name, 'Fingerprint Service Error',
                        'The service for algorithm "%s" version "%s" returned:'
                        '\n\n'
                        '- Status Code: %s\n'
                        '- Reason: %s' % (
                            fingerprint.algorithm, fingerprint.version,
                            request.status_code, request.reason))
                continue

            # parse fingerprint service response
            # TODO: log response
            response = json.loads(request.text)

            # sanity check: low score
            if response['score'] < service['threshold']:
                warning_name = 'lowfingerprintscore,%s' % fingerprint.id
                if Warning.check(warning_name):
                    raise UserWarning(
                        warning_name, 'Low Fingerprint Score',
                        'The fingerprint "%s" cannot be matched, because the '
                        'matching score "%s" is lower than "%s"' % (
                            fingerprint.id, response['score'],
                            service['threshold']))
                fingerprint.matched_state = 'fail_score'
                if fingerprint.state == 'created':
                    fingerprint.state = 'matched'
                fingerprint.save()
                continue

            # sanity check: empty track_id
            if not response['track_id']:
                warning_name = 'nocreationcode,%s' % fingerprint.id
                if Warning.check(warning_name):
                    raise UserWarning(
                        warning_name, 'No Creation Code',
                        'The fingerprint "%s" cannot be matched, because an '
                        'empty creation code was returned.' % fingerprint.id)
                fingerprint.matched_state = 'fail_code'
                if fingerprint.state == 'created':
                    fingerprint.state = 'matched'
                fingerprint.save()
                continue

            # sanity check: unknown creation
            creations = Creation.search([('id', '=', response['track_id'])])
            if not creations:
                warning_name = 'creationnotfound,%s' % fingerprint.id
                if Warning.check(warning_name):
                    raise UserWarning(
                        warning_name, 'Creation Not Found',
                        'The fingerprint "%s" cannot be matched, because the '
                        'corresponding creation code "%s" was not found in '
                        'the database.' % (
                            fingerprint.id, response['track_id']))
                fingerprint.matched_state = 'fail_creation'
                if fingerprint.state == 'created':
                    fingerprint.state = 'matched'
                fingerprint.save()
                continue

            # update fingerprint
            fingerprint.matched_creation = creations[0]
            fingerprint.matched_state = 'success'
            if fingerprint.state == 'created':
                fingerprint.state = 'matched'
            fingerprint.save()

        return 'end'


class DeviceMessageFingerprintMergeStart(ModelView):
    'Device Message Fingerprint Merge Form'
    __name__ = 'device.message.fingerprint.merge.start'
    context = fields.Reference(
        'Context', [
            ('location.space', 'Location Space'),
            ('website.resource', 'Website Resource'),
        ], domain={
            'location.space': [('messages', '!=', None)],
            'website.resource': [('messages', '!=', None)],
        },  # TODO: fingerprints searcher
        states={'required': True}, help='The context')
    states = fields.Boolean(
        'All States', help="Include fingerprints with all states")
    keep_state = fields.Boolean(
        'Keep State', help="Keep the current state of the fingerprints")
    # TODO: change to multi selection after tryton upgrade
    # states = fields.MultiSelection(
    #     fingerprint_states, 'States', sort=False, states={'required': True},
    #     help='The states of the fingerprints to be included in the merge')
    start = fields.DateTime(
        'Start', states={'required': True},
        help='Start of the period of timestamps to merge')
    end = fields.DateTime(
        'End', states={'required': True},
        help='End of the period of timestamps to merge')


class DeviceMessageFingerprintMergeSelect(ModelView):
    'Device Message Fingerprint Select Form'
    __name__ = 'device.message.fingerprint.merge.select'
    # TODO: add utilisation (domain: context) to add the creationlist to
    fingerprints = fields.One2Many(
        'device.message.fingerprint', None, 'Fingerprints',
        states={'required': True}, help='The fingerprints to merge')


class DeviceMessageFingerprintMerge(Wizard):
    'Device Message Fingerprint Merge'
    __name__ = 'device.message.fingerprint.merge'

    # TODO: configuration values
    minimum_duration = datetime.timedelta(seconds=60)
    default_duration = datetime.timedelta(seconds=60*3)

    start = StateView(
        'device.message.fingerprint.merge.start',
        'collecting_society.device_message_fingerprint_merge_start_view_form',
        [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Next', 'select', 'tryton-go-next', default=True),
        ])
    select = StateView(
        'device.message.fingerprint.merge.select',
        'collecting_society.device_message_fingerprint_merge_select_view_form',
        [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Merge', 'merge', 'tryton-go-next', default=True),
        ])
    merge = StateTransition()

    def default_start(self, fields):
        return {
            'states': False,
            'keep_state': False,
            'end': datetime.datetime.now(),
        }

    def default_select(self, fields):
        Fingerprint = Pool().get('device.message.fingerprint')
        order = [('timestamp', 'ASC')]
        domain = [
            ('message.context', '=', str(self.start.context)),
            ('timestamp', '>=', self.start.start),
            ('timestamp', '<=', self.start.end),
        ]

        # TODO: change for multi selection after tryton upgrade
        if not self.start.states:
            domain.append(('state', '=', 'matched'))

        return {
            'fingerprints': [
                fingerprint.id for fingerprint
                in Fingerprint.search(domain, None, None, order)]
        }

    def transition_merge(self):
        # sanity checks
        fingerprints = self.select.fingerprints
        if not fingerprints:
            return 'end'

        # initialize creationlist
        Creationlist = Pool().get('device.message.fingerprint.creationlist')
        Item = Pool().get('device.message.fingerprint.creationlist.item')
        creation_list = Creationlist()
        creation_list.context = self.start.context
        creation_list.start = self.start.start
        creation_list.end = self.start.end
        creation_list.items = []
        creation_list.confirmed = False
        creation_list.utilisation_creationlist = None

        # merge fingerprints
        item = None
        expected_duration = None
        merged_fingerprints = []
        creation_list_items = []
        for fingerprint in fingerprints:

            # skip failed matches
            if fingerprint.matched_state != "success":
                continue

            # aggregate objects
            if item:
                start = merged_fingerprints[0].timestamp
                duration = fingerprint.timestamp - start
                # append fingerprint for same creation within duration
                if fingerprint.matched_creation == item.creation:
                    if duration <= expected_duration:
                        merged_fingerprints.append(fingerprint)
                        continue
                # append item if duration minimum is met
                if duration > self.minimum_duration:
                    item.merged_fingerprints = merged_fingerprints
                    merged_fingerprints = []
                    creation_list_items.append(item)

            # create new item
            item = Item()
            item.creation = fingerprint.matched_creation
            item.order = len(creation_list.items) + 1
            item.timestamp = fingerprint.timestamp
            merged_fingerprints.append(fingerprint)
            expected_duration = self.default_duration
            if item.creation.duration:
                expected_duration = datetime.timedelta(
                    seconds=int(item.creation.duration))

        # save objects
        creation_list.items = creation_list_items
        creation_list.save()
        if not self.start.keep_state:
            for fingerprint in fingerprints:
                fingerprint.state = 'merged'
                fingerprint.save()
        return 'end'


class DeviceMessageFingerprintCreationlist(PublicApi, ModelSQL, ModelView,
                                           CurrentState):
    'Device Message: Fingerprint Creationlist'
    __name__ = 'device.message.fingerprint.creationlist'
    _history = True
    context = fields.Reference(
        'Context', [
            ('location.space', 'Location Space'),
            ('website.resource', 'Website Resource'),
        ], states={'required': True},
        help='The context')
    start = fields.DateTime(
        'Start', states={'required': True},
        help='Start of the period of timestamps to merge')
    end = fields.DateTime(
        'End', states={'required': True},
        help='End of the period of timestamps to merge')
    # TODO: convert fields.Integer to fields.TimeDelta after tryton upgrade
    period = fields.Function(
        fields.Integer('Total [s]'),
        'get_period')
    identified_period = fields.Function(
        fields.Integer('Identified [s]'),
        'get_identified_period')
    unidentified_period = fields.Function(
        fields.Integer('Undentified [s]'),
        'get_unidentified_period')
    # TODO: configuration value
    percentage_precision = 2
    identified_percentage = fields.Function(
        fields.Numeric('Identified [%]', digits=(3, percentage_precision)),
        'get_identified_percentage')
    unidentified_percentage = fields.Function(
        fields.Numeric('Undentified [%]', digits=(3, percentage_precision)),
        'get_unidentified_percentage')
    # TODO: readonly if utilisation_creationlist != None
    confirmed = fields.Boolean(
        'Confirmed', states=STATES, depends=DEPENDS,
        help='The confirmation state by the licensee.')
    items = fields.One2Many(
        'device.message.fingerprint.creationlist.item', 'creation_list',
        'Creation List Items', states=STATES, depends=DEPENDS,
        help='The items within the creation list')

    utilisation_creationlist = fields.Many2One(
        'utilisation.creationlist', 'Utilisation Creation List',
        states=STATES, depends=DEPENDS,
        help='The utilisation creation list resulting from the fingerprints')

    def get_period(self, name):
        if not self.start or not self.end:
            return 0
        period = self.end - self.start
        return int(period.total_seconds())

    def get_identified_period(self, name):
        period = 0.0
        # TODO: configuration value
        default_duration = DeviceMessageFingerprintMerge.default_duration
        default_duration = default_duration.total_seconds()
        for item in self.items:
            if item.creation.duration:
                period += item.creation.duration
            else:
                period += default_duration
        return int(period)

    def get_unidentified_period(self, name):
        return max(0, self.period - self.identified_period)

    def get_identified_percentage(self, name):
        if not self.period:
            return Decimal(0)
        percentage = self.identified_period / Decimal(self.period) * 100
        return percentage.quantize(Decimal(10) ** -self.percentage_precision)

    def get_unidentified_percentage(self, name):
        return Decimal(100.00) - self.identified_percentage


class DeviceMessageFingerprintCreationlistItem(PublicApi, ModelSQL, ModelView):
    'Device Message: Fingerprint Creationlist Item'
    __name__ = 'device.message.fingerprint.creationlist.item'
    _history = True

    creation_list = fields.Many2One(
        'device.message.fingerprint.creationlist', 'Creation List',
        states={'required': True},
        help='The creation list of the creation list item')
    creation = fields.Many2One(
        'creation', 'Creation',
        help='The creation of the creation list item')
    order = fields.Integer(
        'Order', states={'required': True},
        help='The order of the creation within the list of creations')
    timestamp = fields.DateTime(
        'Timestamp', states={'required': True},
        help='The point in time, when the creation was utlized')
    merged_fingerprints = fields.One2Many(
        'device.message.fingerprint', 'merged_creation', 'Fingerprints',
        help='The fingerprints merged into this creation list item')


class DeviceMessageUsagereport(ModelSQL, ModelView, CurrencyDigits,
                               metaclass=IndicatorsMeta):
    'Device Message: Usagereport'
    __name__ = 'device.message.usagereport'
    _history = True

    # Note: The metaclass adds relations to indicators and shortcut function
    #       fields to their attributes to this class (see metaclass docstring)
    __indicators__ = 'website.resource.indicators'
    __samples__ = ['reported']

    device = fields.Function(
        fields.Many2One('device', 'Device'), 'get_device')
    # TODO: 2One interface via fields.Function
    message = fields.One2Many(
        'device.message', 'content', 'Message', states={'required': True},
        domain=[('category', '=', 'usagereport')],
        help='The device message')
    state = fields.Selection(
        [
            ('created', 'Created'),
            ('processed', 'Processed'),
            ('discarded', 'Discarded'),
        ], 'State', sort=False, states={'required': True},
        help='The state of the usage report:\n'
             '- Created: the usage report was created\n'
             '- Processed: the usage report was processed\n'
             '- Discarded: the usage report was discarded')

    timestamp = fields.DateTime(
        'Timestamp', states={'required': True},
        help='The point in time of the utilisation')

    # context dependend fields: dsp
    creation = fields.Many2One(
        'creation', 'Creation',
        # TODO: visible only for message.context = website.resource
        #       and message.context.category = DSP
        help='The creation of the creation list item')

    utilisation_creation_list = fields.Many2One(
        'utilisation.creationlist', 'Utilisation Creation List',
        help='The utilisation creation list resulting from the usage reports')

    def get_device(self, name):
        if self.message:
            return self.message[0].device.id


# --- Declaration ------------------------------------------------------------

context_list = [
    (None, ''),
    ('event', 'Event'),
    ('location', 'Location'),
    ('website', 'Website'),
    ('release', 'Release'),
]


class Declaration(PublicApi, CodeSequence, ModelSQL, ModelView, CurrentState):
    'Declaration'
    __name__ = 'declaration'
    _history = True
    _code_sequence = 'declaration_sequence'

    licensee = fields.Many2One(
        'party.party', 'Licensee', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help="The licensee of the declaration")

    state = fields.Selection(
        [
            ('submitted', 'Submitted'),
            ('canceled', 'Canceled'),
            ('finished', 'Finished'),
        ], 'State', required=True, sort=False,
        states=STATES, depends=DEPENDS,
        help='The state of the declaration')
    next_step = fields.Function(
        fields.Selection([
            (None, 'None'),
            ('utilisation', 'Utilisation'),
            ('estimation', 'Estimation'),
            ('confirmation', 'Confirmation'),
            ('finalization', 'Finalization'),
            ('processing', 'Processing'),
            ('payment', 'Payment'),
        ], 'Awaiting'), 'get_next_step')
    next_step_deadline = fields.Function(
        fields.DateTime(
            'Awaiting Deadline',
            help="Deadline for the next step"),
        'get_next_step_deadline')

    template = fields.Boolean(
        'Template', help='Is this declaration a template?')
    period = fields.Selection(
        [  # in descending order
            ('yearly', 'Yearly'),
            ('quarterly', 'Quarterly'),
            ('monthly', 'Monthly'),
            ('onetime', 'Onetime'),
        ], 'Period', required=True, sort=False,
        states=STATES, depends=DEPENDS,
        help='The period of a recurring declaration.')
    group = fields.Many2One(
        'declaration.group', 'Group', states=STATES, depends=DEPENDS,
        help='The group of the declaration')

    tariff = fields.Many2One(
        'tariff_system.tariff', 'Tariff', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The chosen main tariff for the planned utilisation')
    context = fields.Reference(
        'Context', context_list, states=STATES, depends=DEPENDS,
        help='The context object of the planned utilisation')

    utilisations = fields.One2Many(
        'utilisation', 'declaration', 'Utilisations',
        states=STATES, depends=DEPENDS,
        help='The utilisations created for the declaration')

    @staticmethod
    def default_state():
        return 'submitted'

    @staticmethod
    def default_template():
        return False

    @classmethod
    def order_period(cls, tables):
        table, _ = tables[None]
        order = [period for period, _ in cls.period.selection]
        whens = [(table.period == period, index)
                 for index, period in enumerate(order)]
        return [Case(*whens, else_=len(order))]

    @classmethod
    def create(cls, vlist):
        DistributionPlan = Pool().get('distribution.plan')
        most_recent_distribution_plan = DistributionPlan.search(
            [], 0, 1, [('id', 'DESC')])
        if not most_recent_distribution_plan:
            raise UserError('no_distribution_plan',
                            'No distribution plan available for utilisation.')

        elist = super(Declaration, cls).create(vlist)
        Utilisation = Pool().get('utilisation')
        for entry in elist:
            if entry.utilisations:
                continue
            utilisation = Utilisation(
                declaration=entry,
                licensee=entry.licensee,
                state='created',
                start=entry.create_date,
                tariff=entry.tariff,
                context=entry.context,
                distribution_plan=most_recent_distribution_plan[0].id
            )
            utilisation.save()
        return elist

    def get_rec_name(self, name):
        rec_name = f"{self.context.rec_name}"
        return rec_name

    def get_next_step(self, name):
        if self.state in ['canceled', 'finished']:
            return None

        # TODO: implement for other tariffs
        if self.period != 'onetime':
            return None
        if self.tariff.category.code != 'L':
            return None

        utilisation = self.utilisations[0]
        event = utilisation.context
        if event.end > datetime.datetime.now():
            return 'utilisation'
        if utilisation.state == 'created':
            return 'estimation'
        if utilisation.state == 'estimated':
            return 'confirmation'
        if utilisation.state == 'confirmed':
            return 'finalization'
        if utilisation.state == 'finalized':
            return 'processing'
        if utilisation.state == 'allocated':
            allocation = utilisation.allocation
            if not allocation or not allocation.invoice:
                return 'processing'
            if allocation.invoice.state == 'posted':
                return 'payment'
            if allocation.invoice.state == 'paid':
                return None
            return 'processing'
        return None

    def get_next_step_deadline(self, name):
        # TODO: implement for other tariffs
        if self.period != 'onetime':
            return None
        if self.tariff.category.code != 'L':
            return None

        utilisation = self.utilisations[0]
        event = utilisation.context
        if self.next_step in ['confirmation', 'finalization']:
            return event.end + datetime.timedelta(
                days=UtilisationFinalize.grace_period_days)
        return None

    def permissions(self, web_user, valid_codes=[], derive=False):
        permissions = set()
        if web_user == self.licensee.web_user:
            permissions.update([
                'view_declaration',
                'confirm_declaration',
                'finalize_declaration',
                'cancel_declaration',
            ])
        if valid_codes:
            permissions = permissions.intersection(valid_codes)
        return tuple(permissions)


class DeclarationGroup(PublicApi, ModelSQL, ModelView, CurrentState):
    'Declaration Group'
    __name__ = 'declaration.group'
    _history = True

    name = fields.Char(
        'Name', states=STATES, depends=DEPENDS,
        help='The name of the declaration group')
    declarations = fields.One2Many(
        'declaration', 'group', 'Declarations', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The declarations in this group')


# --- Utilisation ------------------------------------------------------------

class Utilisation(CodeSequence, PublicApi, ModelSQL, ModelView, CurrencyDigits,
                  CurrentState, metaclass=IndicatorsMeta):
    'Utilisation'
    __name__ = 'utilisation'
    _history = True
    _code_sequence = 'utilisation_sequence'

    # Note: The metaclass adds relations to indicators and shortcut function
    #       fields to their attributes to this class (see metaclass docstring)
    __indicators__ = 'utilisation.indicators'
    __samples__ = ['estimated', 'confirmed']

    state = fields.Selection(
        [
            ('created', 'Created'),
            ('estimated', 'Estimated'),
            ('confirmed', 'Confirmed'),
            ('finalized', 'Finalized'),
            ('allocated', 'Allocated'),
        ], 'State', required=True, sort=False,
        states=STATES, depends=DEPENDS,
        help='The processing state of the utilisation:\n\n'
        '*Created*: Default state for new utilisations.\n'
        '*Estimated*: All indicators are present and the utilisation is '
        'awaiting confirmation.\n'
        '*Confirmed*: All indicators were confirmed.\n'
        '*Finalized*: The utilisation is ready to be allocated.\n'
        '*Allocated*: The utilisation was allocated.')
    start_override = fields.DateTime(
        'Start',
        help='Start of the period of utilisation, if setter is used')
    start = fields.Function(
        fields.DateTime(
            'Start', depends=DEPENDS, states={
                'required': True,
            }, help='Start of the period of utilisation'),
        'get_start', 'set_start')
    end_override = fields.DateTime(
        'End',
        help='End of the period of utilisation, if setter is used')
    end = fields.Function(
        fields.DateTime(
            'End', help='End of the period of utilisation'),
        'get_end', 'set_end')
    confirmation = fields.Selection(
        [
            (None, ''),
            ('manual', 'Manually confimed by licensee'),
            ('admin', 'Manually confimed by administrator'),
            ('auto', 'Automatically confimed'),
        ], 'Confirmation', sort=False,
        states=STATES, depends=DEPENDS,
        help='The confirmation state of the utilisation')

    declaration = fields.Many2One(
        'declaration', 'Declaration', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The declaration, which created this utilisation')

    licensee = fields.Many2One(
        'party.party', 'Licensee', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The licensee party')
    context = fields.Reference(
        'Context', context_list, states=STATES, depends=DEPENDS,
        help='The context object of the planned utilisation')
    tariff = fields.Many2One(
        'tariff_system.tariff', 'Tariff', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The resulting tariff for the utilisation')

    creation_list = fields.Many2One(
        'utilisation.creationlist', 'Creationlist',
        states=STATES, depends=DEPENDS,
        help='The creation list for the distribution process')
    distribution_plan = fields.Many2One(
        'distribution.plan', 'Distribution Plan', states={
            'required': True,
            'readonly': ~Eval('active'),
        }, depends=DEPENDS,
        help='The distribution plan for the utilisation')
    collection = fields.Many2One(
        'collection', 'Collection',
        states=STATES, depends=DEPENDS,
        help='The collection of the utilisation')
    allocation = fields.Many2One(
        'allocation', 'Allocation',
        states=STATES, depends=DEPENDS,
        help='The allocation of the utilisation')
    distribution = fields.Many2One(
        'distribution', 'Distribution',
        states=STATES, depends=DEPENDS,
        help='The distribution of the utilisation')

    # context dependend fields: location
    confirmed_location_indicators = fields.Many2One(
        'location.indicators', 'Location Indicators',
        states=STATES, depends=DEPENDS,
        # TODO: visible and required only for context Location
        help='The confirmed location indicators')
    confirmed_location_space_indicators = fields.Many2One(
        'location.space.indicators', 'Location Space Indicators',
        states=STATES, depends=DEPENDS,
        # TODO: visible and required only for context Location
        help='The confirmed location space indicators')

    @staticmethod
    def default_state():
        return 'created'

    @classmethod
    def set_start(cls, utilisations, name, start):
        for utilisation in utilisations:
            # if utilisation.context is not None:
            #     return None
            utilisation.start_override = start
            utilisation.save()

    def get_start(self, name=None):
        if self.context:
            if self.tariff.category.code == 'C':  # reproduction
                if self.context.production_date is not None:  # return proddate
                    return datetime.datetime.combine(
                        self.context.production_date,
                        datetime.time(0, 0, 0, 0)
                    )
            if self.tariff.category.code == 'L':  # live
                return self.context.start  # event start date

        # all other tariffs get the start date from a manually entered date
        return self.start_override

    @classmethod
    def set_end(cls, utilisations, name, end):
        for utilisation in utilisations:
            # if utilisation.context is not None:
            #     return None
            utilisation.end_override = end
            utilisation.save()

    def get_end(self, name=None):
        if self.context:
            if self.tariff.category.code == 'C':  # reproduction
                if self.context.production_date is not None:  # return proddate
                    return datetime.datetime.combine(         # + 1
                        self.context.production_date + datetime.timedelta(
                            days=1),
                        datetime.time(0, 0, 0, 0)
                    )
            if self.tariff.category.code == 'L':  # live
                return self.context.end  # event end date

        # all other tariffs get the end date from a manually entered date
        return self.end_override

    # --- collection ----------------------------------------------------------

    def context_indicators_as_dict(self, sample):
        if self.tariff.category.code == 'L':
            indicators = getattr(self.context, f"{sample}_indicators")
            return {
                'start': indicators.start,
                'end': indicators.end,
                'attendants': indicators.attendants,
                'turnover_tickets': indicators.turnover_tickets,
                'turnover_benefit': indicators.turnover_benefit,
                'expenses_musicians': indicators.expenses_musicians,
                'expenses_production': indicators.expenses_production,
            }
        elif self.tariff.category.code == 'C':
            return {}
        elif self.tariff.category.code == 'P':
            return {}
        elif self.tariff.category.code == 'O':
            return {}
        raise NotImplementedError()

    def calculate_base(self, sample, save=False):
        # sanity checks
        assert sample in ['estimated', 'confirmed']
        # indicators dict
        context_indicators_dict = self.context_indicators_as_dict(sample)
        # represented ratio
        billable_ratio = 1  # TODO: define default
        if self.creation_list:
            billable_ratio = self.creation_list.billable_ratio
        # base
        formula = self.tariff.get_base_formula()
        base = formula(
            context=context_indicators_dict,
            billable_ratio=billable_ratio
        )
        indicators = getattr(self, f"{sample}_indicators")
        indicators.base = base.quantize(
            Decimal(1) / 10 ** self.get_currency_digits('')
        )
        if save:
            indicators.save()
        return base

    def calculate_relevance(self, sample):
        # sanity checks
        assert sample in ['estimated', 'confirmed']
        # indicators dict
        context_indicators_dict = self.context_indicators_as_dict(sample)
        # relevance
        formula = self.tariff.get_relevance_formula()
        utilisation_indicators = getattr(self, f'{sample}_indicators')
        relevance = utilisation_indicators.relevance.value
        return formula(
            context=context_indicators_dict,
            relevance=relevance
        )

    def calculate_share(self, sample):
        # sanity checks
        assert sample in ['estimated', 'confirmed']
        # indicators dict
        context_indicators_dict = self.context_indicators_as_dict(sample)
        # share
        formula = self.tariff.get_share_formula()
        return formula(context=context_indicators_dict)

    def calculate_adjustments(self, sample):
        context_indicators_dict = self.context_indicators_as_dict(sample)
        indicators = getattr(self, f"{sample}_indicators")
        # adjustments_dict
        adjustments_dict = {
            adjustment.category.code: adjustment.value
            for adjustment in indicators.adjustments
            if adjustment.status == "approved"
        }
        # adjustments
        formula = self.tariff.get_adjustments_formula()
        return formula(
            context=context_indicators_dict,
            adjustments=adjustments_dict
        )

    def calculate_invoice_amount(self, sample, save=False):
        indicators = getattr(self, f"{sample}_indicators")
        formula = self.tariff.get_total_formula()
        utilisation_dict = {
            'base': indicators.base,
            'relevance': self.calculate_relevance(sample),
            'share': self.calculate_share(sample),
            'adjustments': self.calculate_adjustments(sample),
        }
        invoice_amount = round(
            formula(utilisation=utilisation_dict),
            self.get_currency_digits('')
        )
        indicators.invoice_amount = invoice_amount
        if save:
            indicators.save()
        return invoice_amount

    def calculate_administration_fee(self, sample, save=False):
        indicators = getattr(self, f"{sample}_indicators")
        formula = self.tariff.get_fee_formula()
        administration_fee = round(
            formula(total=indicators.invoice_amount),
            self.get_currency_digits('')
        )
        indicators.administration_fee = administration_fee
        if save:
            indicators.save()
        return administration_fee

    def calculate_all(self, sample, save=False):
        # TODO: implement calculations for other tariffs
        if self.tariff.category.code not in ['L']:
            return
        self.calculate_base(sample, save)
        self.calculate_invoice_amount(sample, save)
        self.calculate_administration_fee(sample, save)

    def _get_invoice_lines(self):
        '''
        Returns invoice lines for each utilisation
        '''
        pool = Pool()
        InvoiceLine = pool.get('account.invoice.line')

        if self.state != 'allocated':
            return []

        distribution_product = self.tariff.category.distribution_product
        administration_product = self.tariff.category.administration_product
        if not all([distribution_product, administration_product]):
            self.raise_user_error('missing_tariff_product', {
                'tariff_category': self.tariff.category.rec_name})

        distribution_invoice_line = InvoiceLine()
        distribution_invoice_line.product = distribution_product
        distribution_invoice_line.account =  \
            distribution_product.account_revenue_used
        if not distribution_invoice_line.account:
            self.raise_user_error('missing_account_revenue', {
                'product': distribution_product.rec_name,
            })
        distribution_invoice_line.type = 'line'
        distribution_invoice_line.description = '{}: {}'.format(
            'Distribution', self.code)
        distribution_invoice_line.origin = self
        distribution_invoice_line.quantity = 1
        distribution_invoice_line.unit = distribution_product.default_uom
        distribution_invoice_line.unit_price = (
            self.confirmed_distribution_amount
            or distribution_product.list_price)
        distribution_invoice_line.taxes = (
            distribution_product.customer_taxes_used)
        distribution_invoice_line.invoice_type = 'out'

        administration_invoice_line = InvoiceLine()
        administration_invoice_line.product = administration_product
        administration_invoice_line.account =  \
            administration_product.account_revenue_used
        if not administration_invoice_line.account:
            self.raise_user_error('missing_account_revenue', {
                'product': administration_product.rec_name,
            })
        administration_invoice_line.type = 'line'
        administration_invoice_line.description = '{}: {}'.format(
            'Administration', self.code)
        administration_invoice_line.origin = self
        administration_invoice_line.quantity = 1
        administration_invoice_line.unit = administration_product.default_uom
        administration_invoice_line.unit_price = (
            self.confirmed_administration_fee
            or administration_product.list_price)
        administration_invoice_line.taxes =  \
            administration_product.customer_taxes_used
        administration_invoice_line.invoice_type = 'out'

        return [distribution_invoice_line, administration_invoice_line]


class UtilisationCalculate(Wizard):
    'Utilisation Calculate'
    __name__ = 'utilisation.calculate'
    start_state = 'calculate'
    calculate = StateTransition()

    def transition_calculate(self):
        if self.record.state in ['estimated', 'confirmed']:
            self.record.calculate_all(self.record.state, save=True)
        return 'end'


class UtilisationConfirm(Wizard):
    'Utilisation Confirm'
    __name__ = 'utilisation.confirm'

    start_state = 'choose_context'
    choose_context = StateTransition()
    review_event_indicators = StateView(
        'event.indicators',
        'collecting_society.event_indicators_form',
        [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Confirm Event Indicators', 'review_utilisation_indicators',
                   'tryton-go-next', default=True),
        ])
    review_utilisation_indicators = StateView(
        'utilisation.indicators',
        'collecting_society.utilisation_indicators_form',
        [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Confirm Utilisation', 'save',
                   'tryton-go-next', default=True),
        ])
    save = StateTransition()

    @staticmethod
    def _record_as_dict(record, fields):
        values = {}
        for fieldname in fields:
            value = getattr(record, fieldname)
            if isinstance(value, Model):
                if getattr(record.__class__, fieldname)._type == 'reference':
                    value = str(value)
                else:
                    value = value.id
            elif isinstance(value, (list, tuple)):
                value = [r.id for r in value]
            values[fieldname] = value
        return values

    def transition_choose_context(self):
        # sanity checks
        if self.record.state != 'estimated':
            return 'end'
        # choose context
        if self.record.tariff.category.code == 'L':
            return 'review_event_indicators'
        elif self.record.tariff.category.code == 'C':
            return 'end'
        elif self.record.tariff.category.code == 'P':
            return 'end'
        elif self.record.tariff.category.code == 'O':
            return 'end'
        return 'end'

    def value_review_event_indicators(self, fields):
        values = self._record_as_dict(
            self.record.context.estimated_indicators,
            fields
        )
        values['confirmed_events'] = []
        values['estimated_events'] = []
        return values

    def value_review_utilisation_indicators(self, fields):
        pool = Pool()
        self.record.context.confirmed_indicators = self.review_event_indicators
        # copy estimated utilisation indicators
        _UtilisationIndicators = pool.get('utilisation.indicators')
        self.record.confirmed_indicators = _UtilisationIndicators(
            **self._record_as_dict(self.record.estimated_indicators, fields))
        # calculate confirmed utilisation indicators
        self.record.state = 'confirmed'
        self.record.calculate_all('confirmed')

        values = self._record_as_dict(
            self.record.confirmed_indicators,
            fields
        )
        values['confirmed_utilisations'] = []
        values['estimated_utilisations'] = []
        return values

    def transition_save(self):
        if self.record.tariff.category.code == 'L':
            event_indicators = self.review_event_indicators
            event_indicators.confirmed_events = [self.record.context]
            event_indicators.save()
        elif self.record.tariff.category.code == 'C':
            pass
        elif self.record.tariff.category.code == 'P':
            pass
        elif self.record.tariff.category.code == 'O':
            pass

        pool = Pool()
        _TariffAdjustment = pool.get('tariff_system.tariff.adjustment')
        _TariffRelevance = pool.get('tariff_system.tariff.relevance')

        utilisation_indicators = self.review_utilisation_indicators
        utilisation_indicators.confirmed_utilisations = [self.record]
        # create new adjustments
        adjustments = []
        for adjustment in utilisation_indicators.adjustments:
            if adjustment.id > 0:
                adjustments.append(_TariffAdjustment(
                    category=adjustment.category,
                    status=adjustment.status,
                    value=adjustment.value,
                    deviation=adjustment.deviation,
                    deviation_reason=adjustment.deviation_reason,
                    utilisation_indicators=adjustment.utilisation_indicators,
                ))
            else:
                adjustments.append(adjustment)
        utilisation_indicators.adjustments = adjustments
        # create new relevance
        relevance = utilisation_indicators.relevance
        utilisation_indicators.relevance = _TariffRelevance(
            category=relevance.category,
            value=relevance.value,
            deviation=relevance.deviation,
            deviation_reason=relevance.deviation_reason,
            utilisation_indicators=relevance.utilisation_indicators,
        )
        utilisation_indicators.save()

        # recalculate indicators
        self.record.state = 'confirmed'
        self.record.confirmed_indicators.adjustments = adjustments
        self.record.confirmed_indicators.relevance = relevance
        self.record.calculate_all('confirmed', save=True)
        self.record.save()
        return 'end'


class UtilisationFinalize(Wizard):
    'Utilisation Finalize'
    __name__ = 'utilisation.finalize'
    start_state = 'finalize'
    finalize = StateTransition()

    # TODO: configuration setting
    grace_period_days = 6 * 7

    def transition_finalize(self):
        # sanity checks
        if self.record.state != 'confirmed':
            raise UserError(
                'Utilisation not "Confirmed"',
                'The utilisation "%s" is not in the state "confirmed" '
                % (self.record.id))
        # condition: adjustments not on approval
        adjustments = self.record.confirmed_indicators.adjustments
        adjustments_on_approval = []
        for adjustment in adjustments:
            if adjustment.status == "on_approval":
                adjustments_on_approval.append(adjustment)
        if adjustments_on_approval:
            raise UserError(
                'Adjustment on approval',
                'The utilisation "%s" can\'t be finalized as long as '
                'the following adjustments wait for approval: %s'
                % (self.record.id,
                   ", ".join([adjustment.category.name
                              for adjustment in adjustments_on_approval])))
        # choose context
        if self.record.tariff.category.code == 'L':
            self.finalize_live()
        elif self.record.tariff.category.code == 'C':
            return 'end'
        elif self.record.tariff.category.code == 'P':
            return 'end'
        elif self.record.tariff.category.code == 'O':
            return 'end'
        return 'end'

    def finalize_live(self):
        pool = Pool()
        Warning = pool.get('res.user.warning')
        # missing playlists
        performances = self.record.context.performances
        playlist_missing = (
            not performances
            or not any([getattr(performance.playlist, 'items', [])
                        for performance in performances])
        )
        if playlist_missing:
            # wait until the grace period is over
            grace_period_deadline = (
                self.record.context.confirmed_end
                + datetime.timedelta(days=self.grace_period_days)
            )
            if datetime.datetime.now() < grace_period_deadline:
                warning_name = 'utilisationgraceperiod,%s' % self.record.id
                if Warning.check(warning_name):
                    raise UserWarning(
                        warning_name, 'Playlists not submitted yet',
                        'The playlists for utilisation "%s" have not been '
                        'submitted yet. The grace period will end on %s'
                        % (self.record.id, grace_period_deadline))
            # add missing playlist fee
            missing_playlist_fee = any([
                adjustment.category.code == 'missing_playlist_fee'
                for adjustment in self.record.confirmed_indicators.adjustments
            ])
            if not missing_playlist_fee:
                AdjustmentCategory = pool.get(
                    'tariff_system.tariff.adjustment.category')
                Adjustment = pool.get('tariff_system.tariff.adjustment')
                missing_playlist_fee, = AdjustmentCategory.search(
                    ['code', '=', 'missing_playlist_fee'])
                adjustment = Adjustment(
                    category=missing_playlist_fee,
                    status='approved',
                    value=missing_playlist_fee.value_default,
                    utilisation_indicators=self.record.confirmed_indicators
                )
                adjustment.save()

        # generate creation list
        if not playlist_missing:
            _UtilisationCreationlist = pool.get('utilisation.creationlist')
            creation_list = self.record.creation_list
            if not creation_list:
                creation_list = _UtilisationCreationlist(
                    utilisations=[self.record.id])
                creation_list.save()
            creation_list.calculate_all(save=True)
            self.record.creation_list = creation_list
        self.record.calculate_all('confirmed', save=True)
        self.record.state = 'finalized'
        self.record.save()

        return 'end'


class UtilisationCreationlist(ModelSQL, ModelView, CurrencyDigits,
                              metaclass=IndicatorsMeta):
    'Utilisation Creationlist'
    __name__ = 'utilisation.creationlist'
    _history = True

    # Note: The metaclass adds relations to indicators and shortcut function
    #       fields to their attributes to this class (see metaclass docstring)
    __indicators__ = 'website.resource.indicators'
    __samples__ = ['total']

    utilisations = fields.One2Many(
        'utilisation', 'creation_list', 'Utilisations',
        help='The utilisations, in which the list is used to distribute')
    complete = fields.Boolean(
        'Complete', help='Is the creation list complete?')
    # TODO: context still needed?
    context = fields.Reference(
        'Context', [
            ('event.performance', 'Event Performance'),
            ('location.space', 'Location Space'),
            ('website.resource', 'Website Resource'),
            ('release', 'Release'),
            (None, 'None'),
        ],
        help='The context object of the utilisation creation list')
    items = fields.One2Many(
        'utilisation.creationlist.item', 'creationlist',
        'Creation List Items',
        help='The items within the utilisation creation list')

    # creation filter
    known = fields.Function(
        fields.One2Many(
            'utilisation.creationlist.item', None,
            'Known Creation List Items',
            help="The known creation list items"),
        'get_known')
    represented = fields.Function(
        fields.One2Many(
            'utilisation.creationlist.item', None,
            'Represented Creation List Items',
            help="The represented known creation list items"),
        'get_represented')
    billable = fields.Function(
        fields.One2Many(
            'utilisation.creationlist.item', None,
            'Billable Creation List Items',
            help="The billable represented known creation list items"),
        'get_billable')

    # calculated values
    known_ratio = fields.Numeric(
        'Known Ratio', digits=(16, 16),
        help='The ratio of known / all creations [0-1]')
    represented_ratio = fields.Numeric(
        'Represented Ratio', digits=(16, 16),
        help='The ratio of represented / all creations [0-1]')
    billable_ratio = fields.Numeric(
        'Billable Ratio', digits=(16, 16),
        help='The ratio of billable / all creations [0-1]')

    # context dependend fields
    performer = fields.Many2One(
        'artist', 'Performer',
        # TODO: visible only for context EventPerformance
        help='The performing artist')
    fingerprint_creationlists = fields.One2Many(
        'device.message.fingerprint.creationlist',
        'utilisation_creationlist',
        'Fingerprint Creationlists',
        # TODO: visible only for context WebsiteResource|LocationSpace
        help='The merged fingerprint creation lists')

    def get_known(self, name=None):
        items = []
        for item in self.items:
            if item.creation.claim_state == 'revised':
                items.append(item)
        return items

    def get_represented(self, name=None):
        pool = Pool()
        CollectingSociety = pool.get('collecting_society')
        tariff = self.utilisations[0].tariff  # TODO: many2one
        collecting_society = CollectingSociety(1)  # TODO: get from context

        items = []
        for item in self.known:
            for ctc in item.creation.tariff_categories:
                if (ctc.category.code == tariff.category.code
                        and ctc.collecting_society == collecting_society):
                    items.append(item)
                    break
        return items

    def get_billable(self, name=None):
        items = []
        for item in self.represented:
            if item.creation.license.billable:
                items.append(item)
        return items

    def calculate_items(self, save=False):
        # sanity checks
        if not self.utilisations:
            return
        pool = Pool()
        # items
        utilisation = self.utilisations[0]
        if utilisation.tariff.category.code == 'L':
            Item = pool.get('utilisation.creationlist.item')
            items = {}
            performances = utilisation.context.performances
            for performance in performances:
                if not performance.playlist:
                    continue
                for playlist_item in performance.playlist.items:
                    creation_id = playlist_item.creation.id
                    if creation_id not in items:
                        items[creation_id] = Item(
                            creationlist=self,
                            creation=creation_id,
                            weight=0,
                        )
                    items[creation_id].weight += 1
        else:
            return
        # save
        if save:
            Item.delete(self.items)
        self.items = items.values()
        if save:
            self.save()

    def calculate_ratios(self, save=False):
        # sanity checks
        if not self.utilisations:
            return

        # ratios
        weights = {}
        for category in ['items', 'known', 'represented', 'billable']:
            weights[category] = Decimal(sum([
                item.weight for item in getattr(self, category)
            ]))

        self.known_ratio = (
            weights['known'] / weights['items']
        ).quantize(
            Decimal(1) / 10 ** self.__class__.known_ratio.digits[1]
        )

        self.represented_ratio = (
            weights['represented'] / weights['items']
        ).quantize(
            Decimal(1) / 10 ** self.__class__.represented_ratio.digits[1]
        )

        self.billable_ratio = (
            weights['billable'] / weights['items']
        ).quantize(
            Decimal(1) / 10 ** self.__class__.billable_ratio.digits[1]
        )

        # save
        if save:
            self.save()

    def calculate_all(self, save=False):
        self.calculate_items(save)
        self.calculate_ratios(save)


class UtilisationCreationlistItem(ModelSQL, ModelView):
    'Utilisation Creationlist Item'
    __name__ = 'utilisation.creationlist.item'
    _history = True

    creationlist = fields.Many2One(
        'utilisation.creationlist', 'Creation List', states={'required': True},
        help='The utilisation creation list of the items')
    creation = fields.Many2One(
        'creation', 'Creation', states={'required': True},
        help='The utilized creation')
    weight = fields.Integer(
        'Weight', states={'required': True},
        help='The relative weight for the distribution')


##############################################################################
# Archive
##############################################################################

class Storehouse(Code, ModelSQL, ModelView, CurrentState):
    'Storehouse'
    __name__ = 'storehouse'
    _rec_name = 'code'
    _history = True
    details = fields.Text(
        'Details', help='Details of the Storehouse.')
    user = fields.Many2One(
        'res.user', 'User', states={'required': True},
        help='The admin user of the Storehouse.')
    harddisks = fields.One2Many(
        'harddisk', 'storehouse', 'Harddisks',
        help='The harddisks in the Storehouse.')


class HarddiskLabel(CodeSequence, ModelSQL, ModelView, CurrentState):
    'Harddisk Label'
    __name__ = 'harddisk.label'
    _rec_name = 'code'
    _history = True
    _code_sequence = 'harddisk_label_sequence'

    harddisks = fields.One2Many(
        'harddisk', 'label', 'Harddisks',
        help='The harddisks in the Storehouse.')


class Harddisk(ModelSQL, ModelView, CurrentState):
    'Harddisk'
    __name__ = 'harddisk'
    _rec_name = 'uuid_harddisk'
    _history = True
    label = fields.Many2One(
        'harddisk.label', 'Label', states={'required': True},
        help='The Label of the Harddisk.')
    version = fields.Integer(
        'Version', states={'required': True},
        help='The version of a Harddisk Label in the Storehouse.')
    storehouse = fields.Many2One(
        'storehouse', 'Storehouse', states={'required': True},
        help='The Storehouse of the Harddisk.')
    location = fields.Char(
        'Location', help='The local position of the Harddisk.')
    closed = fields.Boolean(
        'Closed', help='The finalization state of the Harddisk.')
    raid_type = fields.Char(
        'Raid Type', states={'required': True}, help='The type of the Raid.')
    raid_number = fields.Char(
        'Raid Number', states={'required': True},
        help='The current number of the harddisk in the Raid.')
    raid_total = fields.Char(
        'Raid Total', states={'required': True},
        help='The total number of harddisks in the Raid.')
    filesystems = fields.One2Many(
        'harddisk.filesystem', 'harddisk', 'Filesystems',
        help='The Filesystems on the Harddisk.')
    uuid_host = fields.Char(
        'Uuid Host', states={'required': True}, help='The uuid of the Host.')
    uuid_harddisk = fields.Char(
        'Uuid Harddisk', states={'required': True},
        help='The uuid of the Harddisk.')
    checksum_harddisk = fields.Many2One(
        'checksum', 'Checksum Harddisk', states={
            'required': Bool(Eval('closed')),
        }, help='The Checksum of the Harddisk.')
    tests = fields.One2Many(
        'harddisk.test', 'harddisk', 'Integrity Tests',
        help='The integrity tests of the Harddisk.')
    user = fields.Many2One(
        'res.user', 'User', states={'required': True},
        help='The admin user, who created the harddisk.')
    online = fields.Boolean(
        'Online', help='The online status of the harddisk.')
    state = fields.Selection(
        [
            ('setup', 'Setup'),
            ('in_use', 'In Use'),
            ('out_of_order', 'Out of Order'),
        ], 'State', required=True, sort=False,
        help='The usage state of the Harddisk.')
    # status = fields.Function(status of last harddisk test)
    # sticker_text = fields.Function(text of sticker with label, etc)
    # sticker_pdf = fields.Function(pdf of sticker with label, etc)


class HarddiskTest(ModelSQL, ModelView):
    'Harddisk Test'
    __name__ = 'harddisk.test'
    _history = True
    harddisk = fields.Many2One(
        'harddisk', 'Harddisk', required=True,
        help='The harddisk which was tested.')
    user = user = fields.Many2One(
        'res.user', 'User', states={'required': True},
        help='The admin user which executed the Test.')
    timestamp = fields.DateTime(
        'Timestamp', required=True,
        help='The point in time of the Test.')
    status = fields.Selection(
        [
            ('sane', 'Sane'),
            ('error_harddisk', 'Harddisk Error'),
            ('error_partition', 'Partition Error'),
            ('error_raid', 'Raid Error'),
            ('error_raid_sub', 'Raid Sub Error'),
            ('error_crypto', 'Crypto Error'),
            ('error_lvm', 'Lvm Error'),
            ('error_filesystem', 'Filesystem Error'),
        ], 'State', required=True, sort=False,
        help='The usage state of the Harddisk.')

    def get_rec_name(self, name):
        return self.harddisk.uuid_harddisk + "@" + str(self.timestamp)


class FilesystemLabel(CodeSequence, ModelSQL, ModelView, CurrentState):
    'Filesystem Label'
    __name__ = 'harddisk.filesystem.label'
    _rec_name = 'code'
    _history = True
    _code_sequence = 'filesystem_label_sequence'

    filesystems = fields.One2Many(
        'harddisk.filesystem', 'label', 'Filesystems',
        help='The Filesystems of the Filesystem Label.')
    contents = fields.One2Many(
        'content', 'filesystem_label', 'Contents',
        help='The Contents of the Filesystem Label.')


class Filesystem(ModelSQL, ModelView, CurrentState):
    'Filesystem'
    __name__ = 'harddisk.filesystem'
    _rec_name = 'uuid_filesystem'
    _history = True
    label = fields.Many2One(
        'harddisk.filesystem.label', 'Label', states={'required': True},
        help='The Label of the Filesystem.')
    harddisk = fields.Many2One(
        'harddisk', 'Harddisk', states={'required': True},
        help='The Harddisk on which the filesystem resides.')
    closed = fields.Boolean(
        'Closed', help='The finalization state of the Filesystem.')
    partition_number = fields.Integer(
        'Partition Number', states={'required': True},
        help='The number of the partition on the Harddisk.')
    uuid_partition = fields.Char(
        'Uuid Partition', states={'required': True},
        help='The uuid of the Partition.')
    uuid_raid = fields.Char(
        'Uuid Raid', states={'required': True},
        help='The uuid of the Raid.')
    uuid_raid_sub = fields.Char(
        'Uuid Raid Sub', states={'required': True},
        help='The uuid of the Raid Sub.')
    uuid_crypto = fields.Char(
        'Uuid Crypto', states={'required': True},
        help='The uuid of the Crypto.')
    uuid_lvm = fields.Char(
        'Uuid Lvm', states={'required': True},
        help='The uuid of the Lvm.')
    uuid_filesystem = fields.Char(
        'Uuid Filesystem', states={'required': True},
        help='The uuid of the Filesystem.')
    checksum_partition = fields.Many2One(
        'checksum', 'Checksum', states={
            'required': Bool(Eval('closed')),
        }, help='The Checksum of the Partition.')
    checksum_raid = fields.Many2One(
        'checksum', 'Checksum', states={
            'required': Bool(Eval('closed')),
        }, help='The Checksum of the Raid.')
    checksum_raid_sub = fields.Many2One(
        'checksum', 'Checksum', states={
            'required': Bool(Eval('closed')),
        }, help='The Checksum of the Raid Sub.')
    checksum_crypto = fields.Many2One(
        'checksum', 'Checksum', states={
            'required': Bool(Eval('closed')),
        }, help='The Checksum of the Crypto.')
    checksum_lvm = fields.Many2One(
        'checksum', 'Checksum', states={
            'required': Bool(Eval('closed')),
        }, help='The Checksum of the Lvm.')
    checksum_filesystem = fields.Many2One(
        'checksum', 'Checksum', states={
            'required': Bool(Eval('closed')),
        }, help='The Checksum of the Filesystem.')


class Content(CodeSequence, UUID, PublicApi, ModelSQL, ModelView, EntityOrigin,
              AccessControlList, CurrentState, CommitState):
    'Content'
    __name__ = 'content'
    _rec_name = 'uuid'
    _history = True
    _code_sequence = 'content_sequence'

    category = fields.Selection(
        [
            ('audio', 'Audio'),
            ('sheet', 'Sheet Music'),
        ], 'Category', required=True, help='The category of content.')
    creation = fields.Many2One(
        'creation', 'Creation', states=STATES, depends=DEPENDS,
        help='The creation associated with the content.')

    # --- FILES --------------------------------------------------------------

    # file metadata
    name = fields.Char(
        'File Name', help='The name of the file.')
    extension = fields.Function(
        fields.Char('Extension'), 'on_change_with_extension')
    size = fields.Integer(
        'Size', help='The size of the content in Bytes.')
    mime_type = fields.Char(
        'Mime Type', help='The media or content type.')
    checksums = fields.One2Many(
        'checksum', 'origin', 'Checksums',
        help='The checksums of the content.')

    # file processing
    path = fields.Char(
        'Path', states={
            'invisible': Eval('processing_state') == 'deleted'
        }, depends=['processing_state'])
    preview_path = fields.Char(
        'Preview Path', states={
            'invisible': Eval('processing_state') == 'deleted'
        }, depends=['processing_state'])
    filesystem_label = fields.Many2One(
        'harddisk.filesystem.label', 'Filesystem Label', states={
            'invisible': Eval('processing_state') != 'archived'
        }, depends=['processing_state'],
        help='The Filesystem Label of the Content.')
    processing_state = fields.Selection(
        [
            (None, ''),
            ('uploaded', 'Upload finished'),
            ('previewed', 'Preview created'),
            ('checksummed', 'Checksum created'),
            ('fingerprinted', 'Fingerprint created'),
            ('dropped', 'Dropped'),
            ('archived', 'Archived'),
            ('deleted', 'Deleted'),
            ('rejected', 'Rejected'),
            ('unknown', 'Unknown'),
        ], 'State', states={'required': True},
        help='The processing state of the content.')
    processing_hostname = fields.Char(
        'Processor', states={
            'invisible': Or(
                Eval('processing_state') == 'deleted',
                Eval('processing_state') == 'archived'
            )
        }, depends=['processing_state'],
        help='The hostname of the processing machine.')
    storage_hostname = fields.Char(
        'Storage', states={
            'invisible': Or(
                Eval('processing_state') == 'deleted',
                Eval('processing_state') == 'archived'
            )
        }, depends=['processing_state'],
        help='The hostname of the storage machine.')
    rejection_reason = fields.Selection(
        [
            (None, ''),
            ('checksum_collision', 'Duplicate Checksum'),
            ('fingerprint_collision', 'Duplicate Fingerprint'),
            ('format_error', 'Format Error'),
            ('no_fingerprint', 'No Fingerprint'),
            ('lossy_compression', 'Lossy Compression'),
            ('missing_database_record', 'Missing Database Record'),
        ], 'Reason', states={
            'invisible': Eval('processing_state') != 'rejected',
            'required': Eval('processing_state') == 'rejected'
        }, depends=['processing_state'],
        help='The reason of the rejection.')
    rejection_reason_details = fields.Text(
        'Details', help='Rejection Explanation',
        states={'invisible': Eval('processing_state') != 'rejected'},
        depends=['processing_state'])
    duplicate_of = fields.Many2One(
        'content', 'Duplicate of',
        domain=[('duplicate_of', '=', None)],
        states={
            'invisible': And(
                Eval('rejection_reason') != 'checksum_collision',
                Eval('rejection_reason') != 'fingerprint_collision'
            ),
            'required': Or(
                Eval('rejection_reason') == 'checksum_collision',
                Eval('rejection_reason') == 'fingerprint_collision',
            )
        }, depends=['rejection_reason'],
        help='The original duplicated Content.')
    duplicates = fields.One2Many(
        'content', 'duplicate_of', 'Duplicates',
        domain=[
            (
                'rejection_reason', 'in',
                ['checksum_collision', 'fingerprint_collision']
            ),
        ], help='The original duplicated Content.')
    mediation = fields.Boolean('Mediation')

    # --- SHEET ---------------------------------------------------------------

    # --- AUDIO ---------------------------------------------------------------

    # low level audio metadata
    length = fields.Float(
        'Length', digits=(16, 6),
        help='The length or duration of the audio content in seconds [s].',
        states={'invisible': Eval('category') != 'audio'},
        depends=['category'])
    channels = fields.Integer(
        'Channels', help='The number of sound channels.',
        states={'invisible': Eval('category') != 'audio'},
        depends=['category'])
    sample_rate = fields.Integer(
        'Sample Rate', help='Sample rate in Hertz [Hz][1/s].',
        states={'invisible': Eval('category') != 'audio'},
        depends=['category'])
    sample_width = fields.Integer(
        'Sample Width', help='Sample width in Bits.',
        states={'invisible': Eval('category') != 'audio'},
        depends=['category'])

    # high level audio metadata
    metadata_artist = fields.Char(
        'Metadata Artist', help='Artist in uploaded metadata.',
        states={'invisible': Eval('category') != 'audio'},
        depends=['category'])
    metadata_title = fields.Char(
        'Metadata Title', help='Title in uploaded metadata.',
        states={'invisible': Eval('category') != 'audio'},
        depends=['category'])
    metadata_release = fields.Char(
        'Metadata Release', help='Release in uploaded metadata.',
        states={'invisible': Eval('category') != 'audio'},
        depends=['category'])
    metadata_release_date = fields.Char(
        'Metadata Release Date', help='Release date in uploaded metadata.',
        states={'invisible': Eval('category') != 'audio'},
        depends=['category'])
    metadata_track_number = fields.Char(
        'Metadata Track Number', help='Track number in uploaded metadata.',
        states={'invisible': Eval('category') != 'audio'},
        depends=['category'])
    fingerprintlogs = fields.One2Many(
        'content.fingerprintlog', 'content', 'Fingerprintlogs',
        help='The fingerprinting log for the content.',
        states={'invisible': Eval('category') != 'audio'},
        depends=['category'])

    # temporary data for analysis
    pre_ingest_excerpt_score = fields.Integer(
        'Pre Ingest Excerpt Score',
        help='Fingerprint match score before ingestion',
        states={'invisible': Eval('category') != 'audio'},
        depends=['category'])
    post_ingest_excerpt_score = fields.Integer(
        'Post Ingest Excerpt Score',
        help='Fingerprint match score after ingestion',
        states={'invisible': Eval('category') != 'audio'},
        depends=['category'])
    uniqueness = fields.Function(
        fields.Float(
            'Uniqueness',
            help='Ratio of fingerprint match score after/before ingestion',
            states={'invisible': Eval('category') != 'audio'},
            depends=['category']),
        'get_uniqueness')
    most_similiar_content = fields.Many2One(
        'content', 'Most Similiar Content',
        help='The most similiar content in our database.',
        states={'invisible': Eval('category') != 'audio'},
        depends=['category'])
    most_similiar_artist = fields.Char(
        'Most Similiar Artist', help='The most similiar artist in echoprint.',
        states={'invisible': Eval('category') != 'audio'},
        depends=['category'])
    most_similiar_track = fields.Char(
        'Most Similiar Track', help='The most similiar track in echoprint.',
        states={'invisible': Eval('category') != 'audio'},
        depends=['category'])

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._order.insert(1, ('name', 'ASC'))

    @staticmethod
    def default_category():
        return 'audio'

    @fields.depends('name')
    def on_change_with_extension(self, name=None):
        if self.name:
            return os.path.splitext(self.name)[1].lstrip('.')

    def get_uniqueness(self, name=None):
        minval = 0.0
        maxval = 100.0
        if not self.post_ingest_excerpt_score:
            return minval
        if not self.pre_ingest_excerpt_score:
            return maxval
        score = self.post_ingest_excerpt_score / float(
            self.pre_ingest_excerpt_score
        )
        return score if score <= maxval else maxval

    @classmethod
    def create(cls, vlist):
        default_roles = [('add', [
            r.id for r in
            AccessRole.search([('name', 'in', DEFAULT_ACCESS_ROLES)])])]

        acls = {}
        elist = super().create(vlist)
        for entry in elist:
            if entry.acl:
                continue
            # always autocreate creator acl
            if entry.entity_creator and entry.entity_creator.web_user:
                acls[entry.entity_creator.web_user.id] = {
                    'entity': str(entry),
                    'web_user': entry.entity_creator.web_user.id,
                    'roles': default_roles
                }
        AccessControlEntry.create(list(acls.values()))

        return elist

    def get_rec_name(self, name):
        result = '%s: %s %s %s %sHz %sBit' % (
            self.name,
            hurry.filesize.size(self.size, system=hurry.filesize.si)
            if self.size else '0M',
            (
                "{:.0f}:{:02.0f}".format(*divmod(self.length, 60))
                if self.length else '00:00'
            ),
            (
                'none' if self.channels in (None, 0) else
                'mono' if self.channels == 1 else
                'stereo' if self.channels == 2 else
                'multi'
            ),
            self.sample_rate if self.sample_rate else '0',
            self.sample_width if self.sample_width else '0',
        )
        return result

    @classmethod
    def search_rec_name(cls, name, clause):
        return [
            'OR',
            ('code',) + tuple(clause[1:]),
            ('uuid',) + tuple(clause[1:]),
            ('name',) + tuple(clause[1:]),
        ]

    def permits(self, web_user, code, derive=True):
        if super().permits(web_user, code, derive):
            return True
        if not derive:
            return False
        derivation = {
            'view_content':   'view_artist_content',
            'edit_content':   'edit_artist_content',
            'delete_content': 'delete_artist_content',
        }
        if self.creation and self.creation.artist:
            for ace in self.creation.artist.acl:
                if ace.web_user != web_user:
                    continue
                for role in ace.roles:
                    for permission in role.permissions:
                        if permission.code == derivation[code]:
                            return True
        return False

    def permissions(self, web_user, valid_codes=[], derive=True):
        direct_permissions = super().permissions(
            web_user, valid_codes, derive)
        if not derive:
            return direct_permissions
        derivation = {
            'view_artist_content':   'view_content',
            'edit_artist_content':   'edit_content',
            'delete_artist_content': 'delete_content',
        }
        if not set(valid_codes).intersection(set(derivation.values())):
            return direct_permissions
        permissions = set(direct_permissions)
        if self.creation and self.creation.artist:
            for ace in self.creation.artist.acl:
                if not derivation:
                    continue
                if ace.web_user != web_user:
                    continue
                for role in ace.roles:
                    for permission in role.permissions:
                        if permission.code in derivation:
                            permissions.add(derivation[permission.code])
                            del derivation[permission.code]
            if valid_codes:
                permissions = permissions.intersection(valid_codes)
        return tuple(permissions)


class Checksum(ModelSQL, ModelView):
    'Checksum'
    __name__ = 'checksum'
    _rec_name = 'code'
    _history = True
    origin = fields.Reference(
        'Origin', [
            ('content', 'Content'),
            ('harddisk', 'Harddisk'),
            ('harddisk.filesystem', 'Filesystem')
        ],
        help='The originating data of the checksum')
    code = fields.Char(
        'Checksum', required=True, help='The string of the Checksum.')
    timestamp = fields.DateTime(
        'Timestamp', states={'required': True},
        help='The point in time of the Checksum.')
    algorithm = fields.Char(
        'Algorithm', states={'required': True},
        help='The algorithm for the Checksum.')
    begin = fields.Integer(
        'Begin', help='The position of the first byte of the Checksum.')
    end = fields.Integer(
        'End', help='The position of the last byte of the Checksum.')


class Fingerprintlog(ModelSQL, ModelView, EntityOrigin):
    'Fingerprintlog'
    __name__ = 'content.fingerprintlog'
    _history = True
    content = fields.Many2One(
        'content', 'Content', required=True, ondelete='CASCADE',
        help='The fingerprinted content.')
    user = fields.Many2One(
        'res.user', 'User', states={'required': True},
        help='The user which fingerprinted the content.')
    timestamp = fields.DateTime(
        'Timestamp', states={'required': True},
        help='Point in time of fingerprinting')
    fingerprinting_algorithm = fields.Char(
        'Algorithm', states={'required': True},
        help='Fingerprinting mechanism of the content, e.g. echoprint')
    fingerprinting_version = fields.Char(
        'Version', states={'required': True},
        help='Fingerprinting algorithm version of the content')


##############################################################################
# Portal
##############################################################################

acl_objects = [
    ('artist', 'Artist'),
    ('release', 'Release'),
    ('creation', 'Creation'),
    ('content', 'Content'),
]


class AccessControlEntry(ModelSQL, ModelView):
    'Access Control Entry'
    __name__ = 'ace'
    _history = True

    web_user = fields.Many2One(
        'web.user', 'Web User', required=True,
        help='The web user interacting with an object.', ondelete='CASCADE')
    party = fields.Function(
        fields.Many2One(
            'party.party', 'Party',
            help='The party of the web user interacting with an object.'
        ), 'get_party')
    entity = fields.Reference(
        'Object', acl_objects, required=True,
        help='The object being interacted with.')
    roles = fields.Many2Many(
        'ace-ace.role', 'ace', 'role', 'Roles',
        states={'required': True},
        help='Individual roles of a party for an object.')
    roles_list = fields.Function(
        fields.Char('Roles'), 'on_change_with_roles_list')

    @fields.depends('roles')
    def on_change_with_roles_list(self, name=None):
        roles = "\n".join([p.name for p in self.roles])
        return roles

    def get_party(self, name):
        return self.web_user.party.id

    @classmethod
    def __setup__(cls):
        super().__setup__()
        table = cls.__table__()
        cls._sql_constraints = [
            ('web_user_entity_uniq',
             Unique(table, table.web_user, table.entity),
             'Error!\nAn ACE for the web user and entity already exists.'),
        ]


class AccessControlEntryRole(ModelSQL, ModelView):
    'Access Control Entry - Access Role'
    __name__ = 'ace-ace.role'
    _history = True

    ace = fields.Many2One(
        'ace', 'Entry', required=True, ondelete='CASCADE')
    role = fields.Many2One(
        'ace.role', 'Role', required=True, ondelete='CASCADE')
    # recursive = fields.Boolean(
    #     'Including Subobjects',  # TODO: require for artist, invisible else
    #     help="Does the role also apply to the subobjects?")


class AccessRole(ModelSQL, ModelView):
    'Access Role'
    __name__ = 'ace.role'
    _history = True

    name = fields.Char(
        'Role', required=True, help='The role of a party regarding an object.')
    description = fields.Text(
        'Description', help='The description of the role.')
    permissions = fields.Many2Many(
        'ace.role-ace.permission', 'role', 'permission', 'Permissions',
        help='Permissions of a role.')
    permissions_list = fields.Function(
        fields.Char('Permissions'), 'on_change_with_permissions_list')

    @fields.depends('permissions')
    def on_change_with_permissions_list(self, name=None):
        permissions = {}
        for permission in self.permissions:
            if permission.entity not in permissions:
                permissions[permission.entity] = []
            permissions[permission.entity].append(permission.name)
        return "\n".join([n for e in permissions for n in permissions[e]])


class AccessRolePermission(ModelSQL, ModelView):
    'Access Role - Access Permission'
    __name__ = 'ace.role-ace.permission'
    _history = True

    role = fields.Many2One(
        'ace.role', 'Role', required=True, ondelete='CASCADE')
    permission = fields.Many2One(
        'ace.permission', 'Permission',
        required=True, ondelete='CASCADE')


class AccessPermission(Code, ModelSQL, ModelView):
    'Access Permission'
    __name__ = 'ace.permission'
    _history = True

    entity = fields.Selection(
        acl_objects, 'Object', required=True, states={'readonly': True},
        help='The object to grant the permission for.')
    name = fields.Char(
        'Role', states={'readonly': True},
        help='The permission to be granted for a role.')
    description = fields.Text(
        'Description', states={'readonly': True},
        help='The description of the permission.')


##############################################################################
# Type Mappings
##############################################################################

AllocationAlias = Allocation
