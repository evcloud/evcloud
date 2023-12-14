from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from compute.models import Host, Center, Group
from network.models import MacIP

User = get_user_model()


class ImageVmCreateFrom(forms.Form):
    data_center = forms.ModelChoiceField(label=_('数据中心'), queryset=Center.objects.all(), required=True,
                                         widget=forms.Select(attrs={'class': 'form-control', 'readOnly': 'true'}))
    group_image = forms.CharField(label=_('宿组机组'), required=True,
                                      widget=forms.Select(attrs={'class': 'form-control', 'readOnly': 'true'}))

    host_image = forms.CharField(label='宿主机', required=True,
                           widget=forms.Select(attrs={'class': 'form-control', 'readOnly': 'true'}))
    vlan_id = forms.CharField(label='vlan', required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    mac_ip = forms.CharField(label='IP地址', required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    vcpu = forms.IntegerField(label='CPU核数', initial=1, required=True,
                              widget=forms.NumberInput(attrs={'class': 'form-control'}))
    mem = forms.IntegerField(label='内存(GB)', initial=1, required=True,
                             widget=forms.NumberInput(attrs={'class': 'form-control'}))
    image_id = forms.IntegerField(label='系统镜像', required=True, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(ImageVmCreateFrom, self).__init__(*args, **kwargs)
        # self.fields['host'].initial = Host.objects.get(ipv4='127.0.0.1')
