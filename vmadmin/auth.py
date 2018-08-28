from django.http import HttpResponseRedirect
from django.contrib.auth.models import User 

def is_staff(request):
    if hasattr(request.user, 'is_staff') and request.user.is_staff:
        return True
    return False

def staff_required(func):
    def _is_staff(request, *args, **argss):
        if is_staff(request):
            return func(request, *args, **argss)
        return HttpResponseRedirect('/accounts/login/?next=%s' % request.path)
    return _is_staff
