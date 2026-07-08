from django.urls import path

from .views import reports_home

app_name = 'reports'

urlpatterns = [
    path('', reports_home, name='home'),
]