#coding=utf-8

from django.contrib.auth.models import User
from api.error import Error, ERR_USERNAME, ERR_USER_DB

class API(object):
    def get_db_user_by_username(self, username):
        user = User.objects.filter(username = username)
        if not user.exists():
            raise Error(ERR_USERNAME)
        return user[0]

    def is_superuser(self, user):
        if type(user) != User:
            raise Error(ERR_USER_DB)
        return user.is_superuser
