from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .manager import VPNManager


class VPNChangeFrom(forms.Form):
    username = forms.CharField(label=_('用户名'), min_length=1, max_length=150, disabled=True, required=False,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label=_('密码'), min_length=6, max_length=64,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    active = forms.BooleanField(label=_('激活状态'), required=False, help_text=_('选中（激活）可用，不选中不可用'))
    remarks = forms.CharField(label=_('备注'), required=False, max_length=255,
                              widget=forms.TextInput(attrs={'class': 'form-control'}))


class VPNAddFrom(forms.Form):
    username = forms.CharField(label=_('用户名'), min_length=1, max_length=150,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label=_('密码'), min_length=6, max_length=64,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    # expired_time = forms.DateTimeField(label='过期时间', widget=forms.DateTimeInput(format=('%Y-%m-%dT%H:%M'), attrs={'class': 'form-control', 'type': 'datetime-local'}))
    active = forms.BooleanField(label=_('激活状态'), required=False, help_text=_('选中（激活）可用，不选中不可用'))
    remarks = forms.CharField(label=_('备注'), required=False, max_length=255,
                              widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean(self):
        d = super().clean()
        username = d['username']
        vpn = VPNManager().get_vpn(username=username)
        if vpn:
            raise ValidationError(_('vpn用户名已存在'))

        return d
