import random
from django.db import models


def get_random_string(length=12, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    """
    Return a securely generated random string.
    """
    return ''.join(random.choice(allowed_chars) for i in range(length))


class VPNAuth(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    username = models.CharField(verbose_name='用户名', max_length=150, unique=True)
    password = models.CharField(verbose_name='密码', max_length=64)
    active = models.BooleanField(verbose_name='激活状态', default=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    modified_time = models.DateTimeField(verbose_name='创建时间', auto_now=True)
    create_user = models.CharField(verbose_name='创建者', max_length=255, default='')
    modified_user = models.CharField(verbose_name='修改者', max_length=255, default='')
    remarks = models.CharField(verbose_name='备注', max_length=255, default='', blank=True)

    class Meta:
        db_table = 'vpn_auth'
        ordering = ['-id']
        verbose_name = 'VPN'
        verbose_name_plural = verbose_name

    def __repr__(self):
        return f'VPN(id={self.id}, username={self.username}, password={self.password})'

    def __str__(self):
        return self.__repr__()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.password:
            self.password = get_random_string()
            if update_fields:
                update_fields = [f for f in update_fields]      # 生成新list, 防止修改外部传入的update_fields
                update_fields.append('password')

        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def set_password(self, p: str, modified_user: str = ''):
        try:
            self.password = p
            if modified_user:
                self.modified_user = modified_user
            self.save(update_fields=['password', 'modified_time', 'modified_user'])
        except Exception as e:
            return False

        return True


