from django.urls import path
from django.views.generic import RedirectView

from .views import admin_dashboard, user_dashboard

app_name = 'dashboard'

urlpatterns = [
    path('', user_dashboard, name='user_dashboard'),
    path('user/', RedirectView.as_view(pattern_name='dashboard:user_dashboard', permanent=False), name='user_dashboard_legacy'),
    path('admin/', admin_dashboard, name='admin_dashboard'),
]
