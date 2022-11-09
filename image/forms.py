from django import forms
from django.contrib.auth import get_user_model

from compute.models import Host
from network.models import MacIP

User = get_user_model()


class ImageVmCreateFrom(forms.Form):
    host = forms.ModelChoiceField(label='宿主机', queryset=Host.objects.filter(ipv4='127.0.0.1').all(), required=True,
                                  widget=forms.Select(attrs={'class': 'form-control', 'readOnly': 'true'}))
    mac_ip = forms.ModelChoiceField(label='IP地址', queryset=MacIP.objects.filter(vlan__image_specialized=True).all(),
                                    required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    vcpu = forms.IntegerField(label='CPU核数', initial=1, required=True,
                              widget=forms.NumberInput(attrs={'class': 'form-control'}))
    mem = forms.IntegerField(label='内存大小', initial=1, required=True,
                             widget=forms.NumberInput(attrs={'class': 'form-control'}))
    image_id = forms.IntegerField(label='系统镜像', required=True, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(ImageVmCreateFrom, self).__init__(*args, **kwargs)
        self.fields['host'].initial = Host.objects.get(ipv4='127.0.0.1')
