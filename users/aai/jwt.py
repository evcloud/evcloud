"""
django-rest-framework-simplejwt
"""
from datetime import datetime, timedelta, timezone
from calendar import timegm
from uuid import uuid4

from jwt import PyJWT
from jwt import (
    InvalidAlgorithmError, InvalidTokenError,
    algorithms
)
from rest_framework.settings import settings
from rest_framework import HTTP_HEADER_ENCODING

from utils.errors import Error


class DictObjectWrapper:
    def __init__(self, d: dict):
        self._d = d

    def __getattr__(self, name):
        return self._d.get(name)

    def __setattr__(self, name, value):
        if name == '_d':
            super().__setattr__(name, value)
            return

        self._d[name] = value


JWT_SETTINGS = DictObjectWrapper(getattr(settings, 'PASSPORT_JWT', None))

AUTH_HEADER_TYPES = JWT_SETTINGS.AUTH_HEADER_TYPES
if not isinstance(AUTH_HEADER_TYPES, (list, tuple)):
    AUTH_HEADER_TYPES = (AUTH_HEADER_TYPES,)

AUTH_HEADER_TYPE_BYTES = set(
    h.encode(HTTP_HEADER_ENCODING)
    for h in AUTH_HEADER_TYPES
)


class JWTInvalidError(Error):
    default_message = "Token is invalid or expired."
    default_code = "InvalidJWT"
    default_status_code = 401


def make_utc(dt):
    if dt.utcoffset() is None:      # 不带时区
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def datetime_to_epoch(dt):
    return timegm(dt.utctimetuple())


def datetime_from_epoch(ts):
    return make_utc(datetime.utcfromtimestamp(ts))


ALLOWED_ALGORITHMS = (
    'HS256',
    'HS384',
    'HS512',
    'RS256',
    'RS384',
    'RS512',
)


class TokenBackend:
    def __init__(self, algorithm, signing_key=None, verifying_key=None, audience=None, issuer=None):
        self._validate_algorithm(algorithm)

        self.algorithm = algorithm
        self.signing_key = signing_key
        self.audience = audience
        self.issuer = issuer
        if algorithm.startswith('HS'):
            self.verifying_key = signing_key
        else:
            self.verifying_key = verifying_key

    @staticmethod
    def _validate_algorithm(algorithm):
        """
        Ensure that the nominated algorithm is recognized, and that cryptography is installed for those
        algorithms that require it
        """
        if algorithm not in ALLOWED_ALGORITHMS:
            raise JWTInvalidError(f"Unrecognized algorithm type '{algorithm}'")

        if algorithm in algorithms.requires_cryptography and not algorithms.has_crypto:
            raise JWTInvalidError(f"You must have cryptography installed to use {algorithm}.")

    def encode(self, payload, headers=None):
        """
        Returns an encoded token for the given payload dictionary.
        """
        jwt_payload = payload.copy()
        if self.audience is not None:
            jwt_payload['aud'] = self.audience
        if self.issuer is not None:
            jwt_payload['iss'] = self.issuer

        token = PyJWT().encode(jwt_payload, self.signing_key, algorithm=self.algorithm, headers=headers)
        if isinstance(token, bytes):
            # For PyJWT <= 1.7.1
            return token.decode('utf-8')
        # For PyJWT >= 2.0.0a1
        return token

    def decode(self, token, verify_signature=True):
        """
        Performs a validation of the given token and returns its payload
        dictionary.
        Raises a `TokenBackendError` if the token is malformed, if its
        signature check fails, or if its 'exp' claim indicates it has expired.
        """
        try:
            return PyJWT().decode_complete(
                token, self.verifying_key, algorithms=[self.algorithm],
                audience=self.audience, issuer=self.issuer,
                options={
                    'verify_aud': self.audience is not None,
                    'verify_signature': verify_signature
                }
            )
        except InvalidAlgorithmError as ex:
            raise JWTInvalidError('Invalid algorithm specified') from ex
        except InvalidTokenError:
            raise JWTInvalidError('Token is invalid or expired')


token_backend = TokenBackend(JWT_SETTINGS.ALGORITHM, JWT_SETTINGS.SIGNING_KEY,
                             JWT_SETTINGS.VERIFYING_KEY, JWT_SETTINGS.AUDIENCE, JWT_SETTINGS.ISSUER)


class Token:
    """
    A class which validates and wraps an existing JWT
    """
    token_type = 'accessToken'
    lifetime = timedelta(hours=1, minutes=5)
    exp_claim = JWT_SETTINGS.EXPIRATION_CLAIM or 'exp'

    def __init__(self, token, verify=True):
        """
        !!!! IMPORTANT !!!! MUST raise a TokenError with a user-facing error
        message if the given token is invalid, expired, or otherwise not safe
        to use.
        """
        if self.token_type is None or self.lifetime is None:
            raise JWTInvalidError('Cannot create token with no type or lifetime')

        self.token = token
        self.current_time = make_utc(datetime.utcnow())

        # Set up token
        if token is not None:
            self.decode_token = token_backend.decode(token, verify_signature=verify)
            self.headers = self.decode_token['header']
            self.payload = self.decode_token['payload']

            if verify:
                self.verify()
        else:
            # New token.  Skip all the verification steps.
            self.headers = {JWT_SETTINGS.TOKEN_TYPE_CLAIM: self.token_type}
            self.payload = {}

            # Set "exp" claim with default value
            self.set_exp(from_time=self.current_time, lifetime=self.lifetime)

            # Set "jti" claim
            self.set_jti()

    def __repr__(self):
        return repr(self.payload)

    def __getitem__(self, key):
        return self.payload[key]

    def __setitem__(self, key, value):
        self.payload[key] = value

    def __delitem__(self, key):
        del self.payload[key]

    def __contains__(self, key):
        return key in self.payload

    def get(self, key, default=None):
        return self.payload.get(key, default)

    def __str__(self):
        """
        Signs and returns a token as a base64 encoded string.
        """
        return token_backend.encode(self.payload)

    def verify(self):
        """
        Performs additional validation steps which were not performed when this
        token was decoded.  This method is part of the "public" API to indicate
        the intention that it may be overridden in subclasses.
        """
        self.check_exp()

        # Ensure token id is present
        # if JWT_SETTINGS.JTI_CLAIM not in self.payload:
        #     raise JWTInvalidError('Token has no id')

        self.verify_token_type()

    def verify_token_type(self):
        """
        Ensures that the token type claim is present and has the correct value.
        """
        try:
            token_type = self.headers[JWT_SETTINGS.TOKEN_TYPE_CLAIM]
        except KeyError:
            raise JWTInvalidError('Token has no type')

        if self.token_type != token_type:
            raise JWTInvalidError('Token has wrong type')

    def set_jti(self):
        """
        Populates the configured jti claim of a token with a string where there
        is a negligible probability that the same string will be chosen at a
        later time.
        See here:
        https://tools.ietf.org/html/rfc7519#section-4.1.7
        """
        self.payload[JWT_SETTINGS.JTI_CLAIM] = uuid4().hex

    def set_exp(self, from_time=None, lifetime=None):
        """
        Updates the expiration time of a token.
        """
        claim = self.exp_claim
        if from_time is None:
            from_time = self.current_time

        if lifetime is None:
            lifetime = self.lifetime

        self.payload[claim] = datetime_to_epoch(from_time + lifetime)

    def check_exp(self, current_time=None):
        """
        Checks whether a timestamp value in the given claim has passed (since
        the given datetime value in `current_time`).  Raises a TokenError with
        a user-facing error message if so.
        """
        claim = self.exp_claim
        if current_time is None:
            current_time = self.current_time

        try:
            claim_value = self.payload[claim]
        except KeyError:
            raise JWTInvalidError(f"Token has no '{claim}' claim")

        try:
            claim_time = datetime_from_epoch(claim_value)
        except ValueError as e:
            raise JWTInvalidError(f"Token '{claim}' claim not valid, {str(e)}")

        if claim_time <= current_time:
            raise JWTInvalidError(f"Token '{claim}' claim has expired")
