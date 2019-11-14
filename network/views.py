from django.shortcuts import render

from .models import Vlan, MacIP

# Create your views here.
def vlan_list(request):
    vlans = Vlan.objects.all()
    return render(request, 'vlan_list.html', {'vlans': vlans})

def vlan_add(request):
    vlan_id = request.GET.get('vlan')
    vlans = Vlan.objects.filter(id=vlan_id)
    return render(request, 'vlan_add.html', {'vlans': vlans})

def vlan_show(request):
    vlan_id = request.GET.get('vlan')
    macips = MacIP.objects.filter(vlan=vlan_id)
    return render(request, 'vlan_show.html', {'macips': macips})