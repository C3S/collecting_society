# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society
from trytond.pool import Pool
from .bank import *
from .collecting_society import *
from .account import *
from .party import *
from .web_user import *
from .configuration import *


def register():
    Pool.register(
        BankAccount,
        BankAccountNumber,
        AccessControlEntry,
        AccessPermission,
        AccessRole,
        AccessRolePermission,
        AccessControlEntryRole,
        CollectingSociety,
        Artist,
        ArtistArtist,
        ArtistPayeeAcceptance,
        ArtistIdentifierName,
        ArtistIdentifier,
        AccountMove,
        AccountMoveLine,
        WebUserRole,
        WebUser,
        WebUserResUser,
        WebUserWebUserRole,
        WebUserParty,
        License,
        Creation,
        CreationDerivative,
        CreationContribution,
        CreationRole,
        CreationIdentifierName,
        CreationIdentifier,
        CreationRightsholder,
        CreationRightsholderCreationRightsholder,
        ArtistPlaylist,
        ArtistPlaylistItem,
        TariffRelevanceCategory,
        TariffRelevance,
        Indicators,
        IndicatorsIndicators,
        IndicatorsEvent,
        IndicatorsLocation,
        IndicatorsLocationSpace,
        IndicatorsWebsiteResource,
        IndicatorsRelease,
        IndicatorsUtilisation,
        TariffSystem,
        TariffAdjustmentCategory,
        TariffAdjustment,
        TariffCategory,
        Tariff,
        CreationTariffCategory,
        Checksum,
        Storehouse,
        HarddiskLabel,
        Harddisk,
        FilesystemLabel,
        Filesystem,
        HarddiskTest,
        Content,
        Fingerprintlog,
        Label,
        Publisher,
        Release,
        ReleaseTrack,
        ReleaseIdentifierName,
        ReleaseIdentifier,
        ReleaseRightsholder,
        ReleaseRightsholderReleaseRightsholder,
        ArtistRelease,
        Instrument,
        CreationRightsholderInstrument,
        Genre,
        ReleaseGenre,
        Style,
        ReleaseStyle,
        CreationContributionRole,
        LocationSpaceCategory,
        LocationCategory,
        Location,
        LocationSpace,
        Event,
        EventPerformance,
        WebsiteCategory,
        WebsiteResourceCategory,
        WebsiteCategoryWebsiteResourceCategory,
        Website,
        WebsiteResource,
        WebsiteResourceCreation,
        Device,
        DeviceAssignment,
        UtilisationCreationlist,
        UtilisationCreationlistItem,
        FingerprintCreationlist,
        FingerprintCreationlistItem,
        DeviceMessage,
        DeviceMessageDeviceMessage,
        Fingerprint,
        Usagereport,
        Distribution,
        DistributionPlan,
        Allocation,
        DeclarationGroup,
        Declaration,
        DeclarationCollection,
        Utilisation,
        DistributeStart,
        Configuration,
        PartyIdentifierName,
        PartyIdentifier,
        Party,
        PartyCategory,
        ContactMechanism,
        Category,
        Address,
        module='collecting_society', type_='model')
    Pool.register(
        Distribute,
        module='collecting_society', type_='wizard')
