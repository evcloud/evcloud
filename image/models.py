#coding=utf-8
from django.db import models
from storage.models import CephPool
app_label = 'image'

class Xml(models.Model):
    name = models.CharField(max_length=100, unique=True)
    xml  = models.TextField()
    desc = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name 

    class Meta:
        app_label = app_label
        verbose_name = '虚拟机XML模板'
        verbose_name_plural = '3_虚拟机XML模板'

class ImageType(models.Model):
    code = models.AutoField('类型编号', primary_key = True)
    name = models.CharField('类型名称', max_length=100, unique = True)
    order= models.IntegerField('排序', default=0, 
        help_text="用于在页面中的显示顺序，数值越小越靠前。")
    
    def __str__(self):
        return self.name 

    class Meta:
        app_label = app_label
        verbose_name = '镜像类型'
        verbose_name_plural = '2_镜像类型'
      
class Image(models.Model):
    cephpool    = models.ForeignKey(CephPool)
    name    = models.CharField(max_length=100)
    version = models.CharField(max_length=100)
    snap    = models.CharField(max_length=200, 
        help_text='系统会通过该字段判断snap是否存在，不存在则自动创建snap并做protect操作。修改或新增snap时请确保镜像没有被任何虚拟机所占用！')
    desc    = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now = True)
    enable  = models.BooleanField(default=True)
    xml     = models.ForeignKey(Xml)
    type    = models.ForeignKey(ImageType)
    # snap_exists = models.BooleanField(default=False)
    order   = models.IntegerField('排序', default=0, 
        help_text="用于在页面中的显示顺序，数值越小越靠前。")

    def __str__(self):
        return self.snap

    class Meta:
        app_label = app_label
        verbose_name = '镜像'
        verbose_name_plural = '1_镜像'
        unique_together = ('cephpool', 'name', 'version')

    @property
    def fullname(self):
        return self.name + ' ' + self.version

    def save(self):
        try:
            from storage.api import StorageAPI
            cephpool = StorageAPI().get_pool_by_id(self.cephpool_id)
            if cephpool:
                if not cephpool.exists(self.snap):
                    create_success = cephpool.create_snap(self.snap)
                    # protect_success = cephpool.protect_snap(self.snap)
                    # if create_success and protect_success:
                    #     self.snap_exists = True
                    # else:
                    #     self.snap_exists = False
        except:
            # self.snap_exists = False
            print('auto create snap error.')
        super(self.__class__, self).save()

    
    



