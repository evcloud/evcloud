#coding=utf-8

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.sessions.backends.cached_db import SessionStore

from api.error import Error
from api.error import ERR_USERNAME
from api.error import ERR_USER_DB
from api.error import ERR_AUTH_LOGIN
from api.error import ERR_AUTH_LOGOUT

class API(object):
    SESSION_KEY = '_auth_user'
    IP_SESSION_KEY = '_auth_ip'
    
    def get_db_user_by_username(self, username):
        user = User.objects.filter(username = username)
        if not user.exists():
            raise Error(ERR_USERNAME)
        return user[0]

    def is_superuser(self, user):
        if type(user) != User:
            raise Error(ERR_USER_DB)
        return user.is_superuser

    def get_session_by_id(self, session_id=None):
        session = SessionStore(session_id)
        return session

    def login(self, username, password, ip, expiry=86400):
        session = self.get_session_by_id()
        user = authenticate(username = username, password = password)
        if user and user.api_user:
            session[self.SESSION_KEY] = user.username
            session[self.IP_SESSION_KEY] = ip
            session.set_expiry(int(expiry))
            session.save()
            return session._session_key
        return False

    def logout(self, session_id):
        try:
            session = self.get_session_by_id(session_id)
            session.delete()
        except Exception as e:
            return False
        return True

