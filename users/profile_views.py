from django.shortcuts import render
from django.urls import reverse

from .decorators import view_mode_allowed
from .remember import get_display_user


@view_mode_allowed
def account_profile(request):
    user = get_display_user(request)
    return render(
        request,
        'users/profile.html',
        {
            'profile_user': user,
            'dashboard_url': reverse('dashboard:admin_dashboard') if user.is_admin_role else reverse('dashboard:user_dashboard'),
        },
    )
