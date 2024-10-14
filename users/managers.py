from django.core import validators

from users.models import UserProfile


class UserManager:
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
