from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.urls import reverse


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), reverse('users:login'))
        if not request.user.is_admin_role:
            return redirect('dashboard:user_dashboard')
        return view_func(request, *args, **kwargs)

    return wrapper


def user_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), reverse('users:login'))
        if request.user.is_admin_role:
            return redirect('dashboard:admin_dashboard')
        return view_func(request, *args, **kwargs)

    return wrapper
