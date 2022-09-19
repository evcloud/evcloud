from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from ceph.models import CephPool
from compute.models import Host
from image.models import Image, VmXmlTemplate
from network.models import MacIP

User = get_user_model()


class ImageModelForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = "__all__"

    def __init__(self, *args, form_type, **kwargs):
        super(ImageModelForm, self).__init__(*args, **kwargs)
        readonly_fields = ['create_time', 'update_time', 'vm_uuid', 'vm_host']
        for field in iter(self.fields):
            if not isinstance(self.fields[field], forms.BooleanField):
                self.fields[field].widget.attrs.update({'class': 'form-control'})
            if field.startswith('vm'):
                self.fields[field].required = True
            if field in readonly_fields:
                self.fields[field].widget.attrs.update({'readOnly': 'true'})
            if form_type == 'add' and field == 'vm_uuid':
                self.fields[field].required = False
        self.fields['vm_mac_ip'].queryset = MacIP.objects.filter(vlan__image_specialized=True).all()
        self.fields['vm_host'] = forms.ModelChoiceField(label='镜像虚拟机宿主机',
                                                        queryset=Host.objects.filter(ipv4='127.0.0.1').all(),
                                                        required=True,
                                                        initial=Host.objects.get(ipv4='127.0.0.1'), widget=forms.Select(
                attrs={'class': 'form-control', 'readOnly': 'true'}))


class ImageVmCreateFrom(forms.Form):
    host = forms.ModelChoiceField(label='镜像虚拟机宿主机', queryset=Host.objects.filter(ipv4='127.0.0.1').all(), required=True,
                                  widget=forms.Select(attrs={'class': 'form-control', 'readOnly': 'true'}))
    mac_ip = forms.ModelChoiceField(label='镜像虚拟机IP', queryset=MacIP.objects.filter(vlan__image_specialized=True).all(),
                                    required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    vcpu = forms.IntegerField(label='CPU核数', initial=1, required=True,
                              widget=forms.NumberInput(attrs={'class': 'form-control'}))
    mem = forms.IntegerField(label='内存大小', initial=1, required=True,
                             widget=forms.NumberInput(attrs={'class': 'form-control'}))
    image_id = forms.IntegerField(label='系统镜像', required=True, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(ImageVmCreateFrom, self).__init__(*args, **kwargs)
        self.fields['host'].initial = Host.objects.get(ipv4='127.0.0.1')

