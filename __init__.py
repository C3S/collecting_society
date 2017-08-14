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
        Artist,
        ArtistArtist,
        ArtistPayeeAcceptance,
        AccountTemplate,
        Account,
        AccountMove,
        AccountMoveLine,
        WebUserRole,
        WebUser,
        WebUserResUser,
        WebUserWebUserRole,
        WebUserParty,
        Client,
        License,

        Creation,
        CreationLicense,

        CreationOriginalDerivative,
        CreationContribution,
        CreationRole,

        # Archiving
        Checksum,
        Storehouse,
        HarddiskLabel,
        Harddisk,
        FilesystemLabel,
        Filesystem,
        HarddiskTest,
        Content,

        Fingerprintlog,
        CreationContent,
        Label,
        Release,
        CreationRelease,
        Genre,
        ReleaseGenre,
        ContributionRole,
        Identification,
        Identifier,
        Distribution,
        Allocation,
        Utilisation,
        UtilisationIMP,
        UtilisationIMPIdentifyStart,
        DistributeStart,
        Configuration,
        Oauth2Client,
        Oauth2RedirectUri,
        Oauth2Code,
        Oauth2Token,
        Party,
        PartyCategory,
        ContactMechanism,
        Category,
        Address,
        module='collecting_society', type_='model')
    Pool.register(
        UtilisationIMPIdentify,
        Distribute,
        module='collecting_society', type_='wizard')
