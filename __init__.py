# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society
from trytond.pool import Pool
from .bank import *
from .collecting_society import *
from .account import *
from .party import *
from .web_user import *
from .oauth import *
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
        Device,
        License,
        Creation,
        CreationDerivative,
        CreationContribution,
        CreationRole,
        CreationIdentifierName,
        CreationIdentifier,
        TariffSystem,
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
        ArtistRelease,
        Genre,
        ReleaseGenre,
        Style,
        ReleaseStyle,
        CreationContributionRole,
        Identification,
        Identifier,
        Distribution,
        Allocation,
        Utilisation,
        DistributeStart,
        Configuration,
        Oauth2Client,
        Oauth2RedirectUri,
        Oauth2Code,
        Oauth2Token,
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
