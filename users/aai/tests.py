from datetime import timezone

from django.test import TestCase
from django.http.request import HttpRequest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from users.models import UserProfile
from ceph.models import GlobalConfig
from . import jwt
from .authentication import AAIJWTAuthentication, JWTInvalidError

utc = timezone.utc


class JWTTestCase(TestCase):
    token = 'eyJ0eXBlIjoiYWNjZXNzVG9rZW4iLCJ0eXAiOiJKV1QiLCJhbGciOiJSUzUxMiJ9.eyJuYW1lIjoi546L546J6aG6IiwiZW1haWwiOiJ3YW5neXVzaHVuQGNuaWMuY24iLCJvcmdOYW1lIjpudWxsLCJjb3VudHJ5IjpudWxsLCJ2b0pzb24iOm51bGwsImlkIjoiMjQ1YmJhZWI3ZjdjZjU0N2U5ZjFjMWMwM2QyNTk4ZWMiLCJleHAiOjE3Mjg3MTk2NzUsImlzcyI6IjI0NWJiYWViN2Y3Y2Y1NDdlOWYxYzFjMDNkMjU5OGVjIiwiaWF0IjoxNzI4NzE2MDc1fQ.fObkCvER6ZEJhFf8-HzuymMo5ho_JwKNUd2YtgNGB9hznxMD-Z0_3yOHG0GhHWIt6SjMq84_RxGoTKM5zM8oY1WoggS07BuhlcP0OCDzdJKRMNC1zrhHL9VqVbpVhfYEewG_BESHLJgVj5Z72ZeXTpsoeE8i-QeTLwBMlTAk9NQ'

    def setUp(self):
        self.rsa = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        bytes_private_key = self.rsa.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        self.private_key = bytes_private_key.decode('utf-8')
        self.public_rsa = self.rsa.public_key()
        bytes_public_key = self.public_rsa.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.public_key = bytes_public_key.decode('utf-8')

    def test_jwt(self):
        token = 'test'
        request = HttpRequest()
        request.META = {'HTTP_AUTHORIZATION': f'AAI-JWT {token}'}
        with self.assertRaises(JWTInvalidError):
            AAIJWTAuthentication().authenticate(request=request)

        token = self.token
        if not self.token:
            return

        self.assertEqual(UserProfile.objects.count(), 0)
        request = HttpRequest()
        request.META = {'HTTP_AUTHORIZATION': f'AAI-JWT {token}'}
        user, t = AAIJWTAuthentication().authenticate(request=request)
        self.assertEqual(UserProfile.objects.count(), 1)
        print(t.payload)
        u = UserProfile.objects.first()
        self.assertEqual(u.username, t["email"])

    def test_jwt_token_backend(self):
        token_backend = jwt.TokenBackend(
            algorithm='RS512', signing_key=self.private_key, verifying_key=self.public_key,
            audience=None, issuer=None
        )
        token = token_backend.encode(
            payload={'username': 'test', 'company': 'cnic', 'age': 18},
            headers={'header1': 'header'}
        )
        r = token_backend.decode(token=token, verify_signature=True)
        payload = r['payload']
        headers = r['header']
        self.assertEqual(payload['username'], 'test')
        self.assertEqual(payload['company'], 'cnic')
        self.assertEqual(payload['age'], 18)
        self.assertEqual(headers['header1'], 'header')

    def test_token(self):
        token_backend = jwt.TokenBackend(
            algorithm='RS512', signing_key=self.private_key, verifying_key=self.public_key,
            audience=None, issuer=None
        )
        token1 = jwt.Token(token=None, backend=token_backend)
        token1['username'] = 'test'
        token = str(token1)
        token2 = jwt.Token(token=token, backend=token_backend)
        self.assertEqual(token2["username"], 'test')

        obj = GlobalConfig(
            name=GlobalConfig.ConfigName.AAI_JWT_VERIFYING_KEY.value,
            content=self.public_key, remark=''
        )
        obj.save(force_insert=True)
        token3 = jwt.Token(token=token)
        self.assertEqual(token3["username"], 'test')
        obj.delete()
