# The COPYRIGHT file at the top level of this repository
# contains the full copyright notices and license terms.

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
        Creation,
        CreationOriginalDerivative,
        CreationContribution,
        CreationRole,
        ContributionRole,
        License,
        CreationLicense,
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
        module='collecting_society', type_='model')
    Pool.register(
        UtilisationIMPIdentify,
        Distribute,
        module='collecting_society', type_='wizard')
