from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import authentication

from .jwt import (JWT_SETTINGS, AUTH_HEADER_TYPES, AUTH_HEADER_TYPE_BYTES,
                  HTTP_HEADER_ENCODING, Token, JWTInvalidError)


class AAIJWTAuthentication(authentication.BaseAuthentication):
    """
    An authentication plugin that authenticates requests through a JSON web
    token provided in a request header.
    """
    www_authenticate_realm = 'api'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_model = get_user_model()

    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)

        return self.get_user(validated_token), validated_token

    def authenticate_header(self, request):
        return '{0} realm="{1}"'.format(
            AUTH_HEADER_TYPES[0],
            self.www_authenticate_realm,
        )

    @staticmethod
    def get_header(request):
        """
        Extracts the header containing the JSON web token from the given
        request.
        """
        header = request.META.get(JWT_SETTINGS.AUTH_HEADER_NAME)

        if isinstance(header, str):
            # Work around django test client oddness
            header = header.encode(HTTP_HEADER_ENCODING)

        return header

    @staticmethod
    def get_raw_token(header):
        """
        Extracts an unvalidated JSON web token from the given "Authorization"
        header value.
        """
        parts = header.split()

        if len(parts) == 0:
            # Empty AUTHORIZATION header sent
            return None

        if parts[0] not in AUTH_HEADER_TYPE_BYTES:
            # Assume the header does not contain a JSON web token
            return None

        if len(parts) != 2:
            raise AuthenticationFailed(
                'Authorization header must contain two space-delimited values',
                code='bad_authorization_header',
            )

        return parts[1]

    @staticmethod
    def get_validated_token(raw_token):
        """
        Validates an encoded JSON web token and returns a validated token
        wrapper object.
        """
        try:
            return Token(raw_token)
        except JWTInvalidError as e:
            extend_msg = f'token_type={Token.token_type}, message={e.args[0]}'
            raise JWTInvalidError(message='Given token not valid for any token type.', extend_msg=extend_msg)

    def get_user(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token[JWT_SETTINGS.USER_ID_CLAIM]
        except KeyError:
            raise JWTInvalidError('Token contained no recognizable user identification')

        params = {JWT_SETTINGS.USER_ID_FIELD: user_id}
        try:
            user = self.user_model.objects.get(**params)
        except self.user_model.DoesNotExist:
            user = self.create_user(validated_token)

        if not user.is_active:
            raise AuthenticationFailed('User is inactive', code='user_inactive')

        return user

    @staticmethod
    def get_first_and_last_name(name: str):
        """
        粗略切分姓和名
        :param name: 姓名
        :return:
            (first_name, last_name)
        """
        if not name:
            return '', ''

        # 如果是英文名
        if name.replace(' ', '').encode('UTF-8').isalpha():
            names = name.rsplit(' ', maxsplit=1)
            if len(names) == 2:
                first_name, last_name = names
            else:
                first_name, last_name = name, ''
        elif len(name) == 4:
            first_name, last_name = name[2:], name[:2]
        else:
            first_name, last_name = name[1:], name[:1]

        # 姓和名长度最大为30
        if len(first_name) > 30:
            first_name = first_name[:31]

        if len(last_name) > 30:
            last_name = last_name[:31]

        return first_name, last_name

    def create_user(self, validated_token):
        try:
            user_id = validated_token[JWT_SETTINGS.USER_ID_CLAIM]
        except KeyError:
            raise JWTInvalidError(f'Token contained no recognizable user identification "{JWT_SETTINGS.USER_ID_CLAIM}"')

        params = {JWT_SETTINGS.USER_ID_FIELD: user_id}
        try:
            truename = validated_token.get(JWT_SETTINGS.TRUE_NAME_FIELD, '')
            first_name, last_name = self.get_first_and_last_name(truename)
        except Exception:
            first_name, last_name = '', ''

        org_name = validated_token.get(JWT_SETTINGS.ORG_NAME_FIELD, '')
        org_name = org_name if org_name else ''
        params.update({'email': user_id, 'first_name': first_name, 'last_name': last_name, 'company': org_name})
        user = self.user_model(**params)
        try:
            user.save()
        except Exception as e:
            raise AuthenticationFailed(_('User create failed') + f';error: {str(e)}', code='user_create_failed')

        return user

