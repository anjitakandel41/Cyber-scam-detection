from django.urls import path

from .views import admin_dashboard, user_dashboard 

app_name = 'dashboard'

urlpatterns = [  
    path('admin/', admin_dashboard, name='admin_dashboard'),
    path('user/', user_dashboard, name='user_dashboard'),
]
