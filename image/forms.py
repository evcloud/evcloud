from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from compute.models import Host, Center, Group
from image.models import Image
from network.models import MacIP, Vlan

User = get_user_model()


class ImageVmCreateFrom(forms.Form):
    data_center = forms.ModelChoiceField(label=_('数据中心'), queryset=Center.objects.none(), required=True,
                                         widget=forms.Select(attrs={'class': 'form-control'}))
    group_image = forms.ModelChoiceField(label=_('宿组机组'), required=True, queryset=Group.objects.none(),
                                         widget=forms.Select(attrs={'class': 'form-control'}))

    host_image = forms.ModelChoiceField(label='宿主机', required=True, queryset=Host.objects.none(),
                                        widget=forms.Select(attrs={'class': 'form-control'}))
    vlan_image = forms.ModelChoiceField(label='vlan', queryset=Vlan.objects.none(), required=True,
                                        widget=forms.Select(attrs={'class': 'form-control'}))
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
        # center_obj = image_obj.get_center()
        try:
            cneter_q = Center.objects.filter(id=image_obj.ceph_pool.ceph.center.id)
        except Exception as e:
            cneter_q = Center.objects.all()

        self.fields['data_center'].queryset = cneter_q
