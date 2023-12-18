from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from compute.models import Host, Center, Group
from image.models import Image
from network.models import MacIP, Vlan

User = get_user_model()


class ImageVmCreateFrom(forms.Form):
    data_center = forms.ModelChoiceField(label=_('数据中心'), queryset=Center.objects.none(), required=True,
                                         widget=forms.Select(attrs={'class': 'form-control', 'readOnly': 'true'}))
    group_image = forms.ModelChoiceField(label=_('宿组机组'), required=True, queryset=Group.objects.none(),
                                         widget=forms.Select(attrs={'class': 'form-control', 'readOnly': 'true'}))

    host_image = forms.ModelChoiceField(label='宿主机', required=True, queryset=Host.objects.none(),
                                        widget=forms.Select(attrs={'class': 'form-control'}))
    vlan_image = forms.ModelChoiceField(label='vlan', queryset=Vlan.objects.none(), required=True,
                                        widget=forms.Select(attrs={'class': 'form-control', 'readOnly': 'true'}))
    mac_ip = forms.ModelChoiceField(label='IP地址', queryset=MacIP.objects.none(), required=True, to_field_name='ipv4',
                                    widget=forms.Select(attrs={'class': 'form-control'}))
    vcpu = forms.IntegerField(label='CPU核数', initial=1, required=True,
                              widget=forms.NumberInput(attrs={'class': 'form-control'}))
    mem = forms.IntegerField(label='内存(GB)', initial=1, required=True,
                             widget=forms.NumberInput(attrs={'class': 'form-control'}))
    image_id = forms.IntegerField(label='系统镜像', required=True, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(ImageVmCreateFrom, self).__init__(*args, **kwargs)
        image_id = self.initial.get('image_id')
        image_obj = Image.objects.filter(id=image_id).first()
        center_obj = image_obj.get_center()

        vlan_q = Vlan.objects.filter(enable=True, image_specialized=True,
                                     group__center_id=center_obj.id).all()  # 一个数据中心一个镜像专用组
        if not vlan_q:
            raise ValueError('请为数据中心设置一个镜像专用组')
        vlan_obj = vlan_q.first()
        group_q = Group.objects.filter(id=vlan_obj.group.id).all()
        group_obj = group_q.first()
        host_q = Host.objects.filter(group_id=group_obj.id).all()
        cneter_q = Center.objects.filter(id=center_obj.id).all()
        mac_ip_q = MacIP.objects.filter(vlan__id=vlan_obj.id).all()

        self.fields['data_center'].initial = center_obj
        self.fields['data_center'].queryset = cneter_q
        self.fields['vlan_image'].initial = vlan_obj
        self.fields['vlan_image'].queryset = vlan_q
        self.fields['group_image'].initial = group_obj
        self.fields['group_image'].queryset = group_q
        self.fields['host_image'].queryset = host_q
        self.fields['mac_ip'].queryset = mac_ip_q

        # self.fields['host'].initial = Host.objects.get(ipv4='127.0.0.1')
