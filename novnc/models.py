from django.db import models

class Token(models.Model):
    token = models.CharField(max_length=64,unique=True)
    ip    = models.CharField(max_length=64)
    port  = models.CharField(max_length=32)
    createtime = models.DateTimeField(auto_now_add=True)
    updatetime = models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.token

    class Meta:
        verbose_name = 'novnc tokens'
        verbose_name_plural = 'novnc tokens'
        #unique_together = ('ip', 'port')

