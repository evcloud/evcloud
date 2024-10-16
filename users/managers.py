from typing import List

from django.core import validators
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.translation import gettext as _

from utils import errors
from users.models import UserProfile


class UserManager:
    @staticmethod
    def is_valid_username(val: str, min_length: int = 4, max_length: int = 150) -> bool:
        if not (min_length <= len(val) <= max_length):
            return False

        try:
            UnicodeUsernameValidator()(val)
        except validators.ValidationError:
            return False

        return True

    @staticmethod
    def is_email_address(val: str) -> bool:
        try:
            validators.validate_email(val)
        except validators.ValidationError:
            return False

        return True

    @staticmethod
    def get_or_create_user(username: str):
        """
        查询或创建用户
        :return:
            UserProfile()

        :raises: Exception
        """
        user = UserProfile.objects.filter(username=username).first()
        if user:
            return user

        user = UserProfile(username=username, is_active=True, is_staff=False, is_superuser=False)
        try:
            user.save(force_insert=True)
        except Exception as exc:
            user = UserProfile.objects.filter(username=username).first()
            if user:
                return user

            raise exc

        return user

    @staticmethod
    def get_or_create_users(usernames: List[str]) -> List[UserProfile]:
        """
        确保用户都存在

        :raises: Error
        """
        users = []
        exists_usernames = set()
        # 先查询已存在的用户
        user_qs = UserProfile.objects.filter(username__in=usernames).all()
        for u in user_qs:
            users.append(u)
            exists_usernames.add(u.username)

        # 创建不存在的用户
        not_found_usernames = list(set(usernames).difference(exists_usernames))
        for username in not_found_usernames:
            if not UserManager.is_valid_username(val=username):
                raise errors.InvalidParamError(
                    msg=_('用户名无效，长度为4-150个字符，只能包含字母、数字、特殊字符“@”、“.”、“-”和“_”'))

            try:
                user = UserManager.get_or_create_user(username=username)
            except Exception as exc:
                raise errors.Error(msg=_('创建用户时错误。') + str(exc))

            users.append(user)

        return users
