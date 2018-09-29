#coding=utf-8
from django.db import models


class SiteConfig(models.Model):
    name = models.CharField(max_length=100,verbose_name="站点显示名称")
    pro_enable = models.BooleanField(default=False,verbose_name="开启高阶功能")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "站点配置"
        verbose_name_plural = "站点配置列表"