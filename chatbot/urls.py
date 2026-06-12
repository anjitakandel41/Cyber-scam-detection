from django.urls import path

from .views import chatbot_home

app_name = 'chatbot'

urlpatterns = [
    path('', chatbot_home, name='home'),
]
