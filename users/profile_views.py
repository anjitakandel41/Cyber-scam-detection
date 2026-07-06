from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse


@login_required
def account_profile(request):
    user = request.user
    return render(
        request,
        'users/profile.html',
        {
            'profile_user': user,
            'dashboard_url': reverse('dashboard:admin_dashboard') if user.is_admin_role else reverse('dashboard:user_dashboard'),
        },
    )
