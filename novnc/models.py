from django.db import models


class Token(models.Model):
    token = models.CharField(max_length=64, unique=True)
    ip = models.CharField(max_length=64, verbose_name='宿主机ip')
    port = models.CharField(max_length=32, verbose_name='vnc端口')
    createtime = models.DateTimeField(auto_now_add=True)
    updatetime = models.DateTimeField(auto_now=True)
    expiretime = models.DateTimeField(verbose_name='过期时间')
    desc = models.CharField(verbose_name='简介', max_length=200, default='', blank=True)

    def __str__(self):
        return self.token

    class Meta:
        verbose_name = 'novnc tokens'
        verbose_name_plural = 'novnc tokens'
