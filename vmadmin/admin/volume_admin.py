#codign=utf-8
from .base import VMModelAdmin
from django import forms 
from compute.models import Group
from volume.models import DBCephQuota, DBCephVolume


class CephVolumeForm(forms.ModelForm):
    size_g = forms.IntegerField(label='容量(GB)')
    
    class Meta:
        model = DBCephVolume
        fields = ['uuid', 'user', 'group', 'creator', 'size_g', 'remarks', 'vm', 'attach_time', 'dev', 'enable', 'cephpool']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['size_g'].initial = self.instance.size_g

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        instance.size = self.cleaned_data['size_g'] * 1024
        instance.save()
        return instance


class CephVolumeAdmin(VMModelAdmin):
    list_display = ('uuid', 'user', 'group', 'cephpool', 'creator', 'create_time', 'size_g',
        'remarks', 'vm', 'attach_time', 'dev', 'enable')
    ordering = ('create_time',)
    form = CephVolumeForm


class CephQuotaForm(forms.ModelForm):
    total_g = forms.IntegerField(label='集群总容量(GB)')
    volume_g = forms.IntegerField(label='云硬盘最大容量(GB)')

    class Meta:
        model = DBCephQuota
        fields = ['group', 'cephpool', 'total_g', 'volume_g']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['total_g'].initial = self.instance.total_g
        self.fields['volume_g'].initial = self.instance.volume_g

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        instance.total = self.cleaned_data['total_g'] * 1024
        instance.volume = self.cleaned_data['volume_g'] * 1024
        instance.save()
        return instance


class CephQuotaAdmin(VMModelAdmin):
    list_display = ('group','cephpool','total_g','volume_g')
    ordering = ('group',)
    form = CephQuotaForm
