# This work is based on work of Elliot Peele <elliot@bentlogic.net> under
# MIT License.
# S.a. https://github.com/elliotpeele/pyramid_oauth2_provider file models.py
import time
from datetime import datetime

from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from .generators import gen_token
from .generators import gen_client_id
from .generators import gen_client_secret


__all__ = [
    'Oauth2Client',
    'Oauth2RedirectUri',
    'Oauth2Code',
    'Oauth2Token',
]
__metaclass__ = PoolMeta


class Oauth2Client(ModelSQL, ModelView):
    'Oauth2 Provider Client'
    __name__ = 'oauth2.provider.client'
    _rec_name = 'client_id'
    client_id = fields.Char('Client Id')
    client_secret = fields.Char('Client Secret', required=True)
    revoked = fields.Boolean('Revoked')
    revocation_date = fields.DateTime('Revocation Date')
    redirect_uris = fields.One2Many(
        'oauth2.provider.redirect_uri', 'client', 'Redirect URIs')
    tokens = fields.One2Many(
        'oauth2.provider.token', 'client', 'Tokens')

    # def __init__(self):
    #    self.client_id = gen_client_id()
    #    self.client_secret = gen_client_secret()

    @classmethod
    def __setup__(cls):
        super(Oauth2Client, cls).__setup__()
        cls._sql_constraints += [
            (
                'client_secret_uniq', 'UNIQUE(client_secret)',
                'The client_secret must be unique.'),
        ]

    @staticmethod
    def default_client_id():
        return gen_client_id()

    @staticmethod
    def default_client_secret():
        return gen_client_secret()

    @staticmethod
    def default_revoked():
        return False

    def revoke(self):
        Date = Pool().get('ir.date')
        date = Date.today()
        self.revoked = True

        self.revocation_date = date

    def isRevoked(self):
        return self.revoked


class Oauth2RedirectUri(ModelSQL, ModelView):
    'Oauth2 Provider Redirect URI'
    __name__ = 'oauth2.provider.redirect_uri'
    _rec_name = 'uri'
    uri = fields.Char('URI', required=True)
    # client_id = fields.(Integer, ForeignKey(Oauth2Client.id))
    client = fields.Many2One('oauth2.provider.client', 'Client')

    # def __init__(self, client, uri):
    #     self.client = client
    #     self.uri = uri

    @classmethod
    def __setup__(cls):
        super(Oauth2RedirectUri, cls).__setup__()
        cls._sql_constraints += [
            (
                'uri_uniq', 'UNIQUE(uri)',
                'The uri must be unique.'),
        ]

    @staticmethod
    def default_client_id():
        return gen_client_id()


class Oauth2Code(ModelSQL, ModelView):
    'Oauth2 Provider Code'
    __name__ = 'oauth2.provider.code'
    _rec_name = 'user_id'

    user_id = fields.Integer('User ID', required=True)
    # web_user = fields.Many2One('web.user', 'Web User')
    authcode = fields.Char('Authcode', required=True)
    expires_in = fields.Integer('Expires in', required=False)
    revoked = fields.Boolean('Revoked')
    revocation_date = fields.DateTime('Revocation Timestamp')
    # This field is created implicit in Tryton create_date:
    # creation_date = fields.DateTime(default=datetime.utcnow)
    # client_id = fields.(Integer, ForeignKey(Oauth2Client.id))
    client = fields.Many2One('oauth2.provider.client', 'Client')

    # def __init__(self, client, user_id):
    #    self.client = client
    #    self.user_id = user_id
    #    self.authcode = gen_token(self.client)

    @classmethod
    def __setup__(cls):
        super(Oauth2Code, cls).__setup__()
        cls._sql_constraints += [
            (
                'authcode_uniq', 'UNIQUE(authcode)',
                'The authcode must be unique.'),
        ]

    @staticmethod
    def default_expires_in():
        return 10 * 60

    @staticmethod
    def default_revoked():
        return False

    def get_authcode(self, client):
        return gen_token(self.client)

    def revoke(self):
        Date = Pool().get('ir.date')
        date = Date.today()
        self.revoked = True
        self.revocation_date = date

    def isRevoked(self):
        expiry = time.mktime(self.create_date.timetuple()) + self.expires_in
        if datetime.frometimestamp(expiry) < datetime.utcnow():
            self.revoke()
        return self.revoked


class Oauth2Token(ModelSQL, ModelView):
    'Oauth2 Provider Token'
    __name__ = 'oauth2.provider.token'
    user_id = fields.Integer('User ID', required=True)
    access_token = fields.Char('Access Token', required=True)
    refresh_token = fields.Char('Refresh Token', required=True)
    expires_in = fields.Integer('Expires in', required=True)
    revoked = fields.Boolean('Revoked')
    revocation_date = fields.DateTime('Revocation Date')
    # This field is created implicit in Tryton create_date:
    # creation_date = fields.DateTime('Creation Date', default=datetime.utcnow)
    # client_id = fields.(Integer, ForeignKey(Oauth2Client.id))
    client = fields.Many2One('oauth2.provider.client', 'Client')

    # def __init__(self, client, user_id):
    #    self.client = client
    #    self.user_id = user_id
    #    self.access_token = gen_token(self.client)
    #    self.refresh_token = gen_token(self.client)

    @classmethod
    def __setup__(cls):
        super(Oauth2Token, cls).__setup__()
        cls._sql_constraints += [
            (
                'uri_access_token', 'UNIQUE(access_token)',
                'The access token must be unique.'),
            (
                'uri_refresh_token', 'UNIQUE(refresh_token)',
                'The refresh token must be unique.'),
        ]

    @staticmethod
    def default_expires_in():
        return 60 * 60

    @staticmethod
    def default_revoked():
        return False

    def get_access_token(self, client):
        return gen_token(client)

    def revoke(self):
        Date = Pool().get('ir.date')
        date = Date.today()

        self.revoked = True
        self.revocation_date = date

    def isRevoked(self):
        expiry = time.mktime(self.creation_date.timetuple()) + self.expires_in
        if datetime.fromtimestamp(expiry) < datetime.utcnow():
            self.revoke()
        return self.revoked

    def refresh(self):
        """
        Generate a new token for this client.
        """

        cls = self.__class__
        self.revoke()
        return cls(self.client, self.user_id)

    def asJSON(self, **kwargs):
        token = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'user_id': self.user_id,
            'expires_in': self.expires_in,
        }
        kwargs.update(token)
        return kwargs
