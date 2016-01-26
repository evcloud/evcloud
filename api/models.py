#coding=utf-8

########################################################################
#@author:   bobfu
#@email:    fubo@cnic.cn
#@date:     2015-10-16
#@desc:     API模块的model
########################################################################

from django.db import models
    
class Log(models.Model):
    user = models.CharField(max_length=100)
    op = models.CharField(max_length=50)
    start_time = models.DateTimeField()
    finish_time = models.DateTimeField()
    result = models.BooleanField()
    error = models.TextField(null=True, blank=True)
    from_trd_part = models.BooleanField(default=False)
    args = models.TextField(null=True, blank=True)
    class Meta:
        verbose_name = 'API日志'
        verbose_name_plural = '2_API日志'
    


